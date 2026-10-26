"""Provider-backed, fail-closed task plan validation for opt-in live runs."""

import json
import random
import time

ALLOWED_STEPS = {"triage", "draft_reply"}


def validate_plan(text: str) -> list[str]:
    try:
        value = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise ValueError("Groq plan is not valid JSON") from exc
    steps = value.get("steps") if isinstance(value, dict) else None
    if (
        not isinstance(steps, list)
        or not 1 <= len(steps) <= 2
        or any(step not in ALLOWED_STEPS for step in steps)
        or len(set(steps)) != len(steps)
    ):
        raise ValueError("Groq plan must contain one or two unique allowlisted steps")
    if steps[0] != "triage":
        raise ValueError("Groq plan must begin with triage")
    return steps


class GroqWorkflowRunner:
    """Optional callable for real, bounded triage and draft steps."""

    model = "openai/gpt-oss-20b"

    def __init__(self, api_keys, policy, *, client_factory=None, budget_usd=0.009):
        if not api_keys or budget_usd <= 0:
            raise ValueError("credentials and a positive budget are required")
        self.keys = list(dict.fromkeys(api_keys))[:4]
        self.policy = policy
        self.client_factory = client_factory or self._new_client
        self.budget_usd = budget_usd
        self.calls = self.attempts = self.input_tokens = self.output_tokens = 0
        self.estimated_cost_usd = 0.0
        self.actual_model = self.model

    @staticmethod
    def _new_client(key):
        from groq import Groq

        return Groq(api_key=key, max_retries=0, timeout=20)

    def __call__(self, payload, step):
        if step not in ALLOWED_STEPS:
            raise ValueError("workflow step is not allowlisted")
        prompt = (
            self.policy
            + "\n"
            + json.dumps(
                {
                    "step": step,
                    "request": payload.get("request", "Synthetic tracking question."),
                }
            )
        )
        estimate = (len(prompt.encode("utf-8")) * 0.075 + 256 * 0.30) / 1_000_000
        if self.estimated_cost_usd + estimate * len(self.keys) > self.budget_usd:
            raise RuntimeError("workflow budget preflight blocked the request")
        for index, key in enumerate(self.keys):
            self.attempts += 1
            try:
                response = self.client_factory(key).chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=256,
                    reasoning_effort="low",
                    temperature=1,
                )
                break
            except Exception as exc:
                self.estimated_cost_usd += estimate
                status = getattr(exc, "status_code", None)
                transient = status in {408, 409, 429, 500, 502, 503, 504} or type(
                    exc
                ).__name__ in {"APITimeoutError", "APIConnectionError", "TimeoutError"}
                if not transient or index + 1 >= len(self.keys):
                    raise RuntimeError(
                        f"workflow provider failure ({type(exc).__name__}, status={status})"
                    ) from None
                headers = getattr(getattr(exc, "response", None), "headers", {})
                raw = headers.get("retry-after") if status == 429 else None
                try:
                    delay = (
                        float(raw)
                        if raw is not None
                        else min(0.25 * 2**index + random.random() * 0.1, 2)
                    )
                except (TypeError, ValueError):
                    delay = min(0.25 * 2**index + random.random() * 0.1, 2)
                if not 0 <= delay <= 2:
                    raise RuntimeError(
                        "workflow retry-after exceeds wait ceiling"
                    ) from None
                time.sleep(delay)
        self.calls += 1
        self.actual_model = getattr(response, "model", self.model)
        if self.actual_model != self.model:
            raise RuntimeError("provider returned an unexpected workflow model")
        self.input_tokens += response.usage.prompt_tokens
        self.output_tokens += response.usage.completion_tokens
        self.estimated_cost_usd += (
            response.usage.prompt_tokens * 0.075
            + response.usage.completion_tokens * 0.30
        ) / 1_000_000
        if self.estimated_cost_usd > self.budget_usd:
            raise RuntimeError("observed workflow usage exceeded budget")
        value = json.loads(response.choices[0].message.content or "")
        field = "category" if step == "triage" else "response"
        if (
            not isinstance(value, dict)
            or not isinstance(value.get(field), str)
            or not value[field].strip()
        ):
            raise ValueError(
                "workflow provider output does not match the step contract"
            )
        return {field: value[field]}
