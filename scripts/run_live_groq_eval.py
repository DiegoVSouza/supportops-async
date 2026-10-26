"""Generate one synthetic task plan with Groq and execute it locally."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import UTC, datetime
from pathlib import Path

from groq import Groq

from supportops_async.live_groq import validate_plan
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_async.worker.runner import FakeRunner

PROJECT = Path(__file__).resolve().parents[1]
LAB = Path(__file__).resolve().parents[3]
MODEL = "openai/gpt-oss-20b"


def load_credentials() -> list[str]:
    for line in (LAB / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            name = name.strip()
            if (
                name.startswith("GROQ_API_KEY")
                and value.strip()
                and name not in os.environ
            ):
                os.environ[name] = value.strip().strip("\"'")
    return list(
        dict.fromkeys(
            os.getenv(n, "").strip()
            for n in [f"GROQ_API_KEY_{i}" for i in range(1, 5)]
            if os.getenv(n, "")
        )
    )


def available_model_keys(api_keys: list[str]) -> list[str]:
    available = []
    for key in api_keys:
        client = Groq(api_key=key, max_retries=0, timeout=20)
        if any(item.id == MODEL for item in client.models.list().data):
            available.append(key)
    return available


def retry_delay(attempt: int, status: int | None, headers) -> float:
    try:
        delay = (
            float(headers.get("retry-after"))
            if status == 429 and headers.get("retry-after")
            else min(0.25 * 2**attempt + random.random() * 0.1, 2)
        )
    except (TypeError, ValueError):
        delay = min(0.25 * 2**attempt + random.random() * 0.1, 2)
    if not 0 <= delay <= 2:
        raise RuntimeError("retry-after exceeds 2 second cap") from None
    return delay


def request_plan(available: list[str]):
    prompt = 'For the synthetic support request "How do I find the tracking link for a delayed parcel?", return JSON only as {"steps":["triage","draft_reply"]}. Use only the listed step names, in that order; no external action or refund.'
    response = None
    for attempt, key in enumerate(available[:4]):
        try:
            response = Groq(
                api_key=key, max_retries=0, timeout=20
            ).chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=128,
                temperature=1,
                reasoning_effort="low",
            )
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status not in {408, 409, 429, 500, 502, 503, 504} and type(
                exc
            ).__name__ not in {"Timeout", "APIConnectionError"}:
                raise RuntimeError(
                    f"provider rejection: {type(exc).__name__}, status={status}"
                ) from None
            if attempt >= min(3, len(available) - 1):
                raise RuntimeError("transient retry limit reached") from None
            headers = getattr(getattr(exc, "response", None), "headers", {})
            delay = retry_delay(attempt, status, headers)
            time.sleep(delay)
    return response


def run_plan(plan: list[str]) -> dict[str, bool]:
    store = SQLiteTaskStore(":memory:")
    broker = InMemoryBroker()
    task, _ = store.create(
        {"steps": plan, "operation_id": "synthetic-p04-plan"}, "phase-013-live-plan"
    )
    broker.publish(BrokerMessage(task.task_id))
    worker = Worker(store, broker, runner=FakeRunner())
    ran = worker.run_once()
    completed = store.get(task.task_id)
    effects = [
        store.effect(task.task_id, f"{i}:{step}") for i, step in enumerate(plan, 1)
    ]
    checks = {
        "allowlisted_plan": True,
        "worker_ran": ran,
        "completed": completed.status.value == "done",
        "one_effect_per_step": len(effects) == len(plan) and all(effects),
        "steps": plan == ["triage", "draft_reply"],
    }
    store.close()
    return checks


def write_result(result: dict[str, object], code: int) -> None:
    evidence_dir = PROJECT / "artifacts" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (evidence_dir / f"phase-013-groq-{timestamp}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence_dir / f"phase-013-groq-{timestamp}.txt").write_text(
        f"Command: LLM_MODE=live uv run --extra live --group dev python scripts/run_live_groq_eval.py\nExit code: {code}\nSanitized result: {json.dumps(result, sort_keys=True)}\n",
        encoding="utf-8",
    )


def main() -> int:
    result = {
        "provider": "groq",
        "model": MODEL,
        "status": "INCOMPLETE",
        "exit_code": 1,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "cost_usd": "PENDING",
    }
    code = 1
    try:
        if os.getenv("LLM_MODE", "").lower() != "live":
            raise RuntimeError("explicit LLM_MODE=live required")
        credentials = load_credentials()
        result["credential_count"] = len(credentials)
        available = available_model_keys(credentials)
        result["model_available_key_count"] = len(available)
        if not available:
            raise RuntimeError("requested model unavailable in authenticated catalog")
        response = request_plan(available)
        plan = validate_plan(response.choices[0].message.content or "")
        checks = run_plan(plan)
        code = 0 if all(checks.values()) else 1
        usage = response.usage
        result.update(
            status="PASS" if code == 0 else "FAIL",
            assertions=checks,
            step_count=len(plan),
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            actual_model=response.model,
        )
    except Exception as exc:
        result["error"] = {"class": type(exc).__name__}
        code = 1
    result.update(exit_code=code, finished_at_utc=datetime.now(UTC).isoformat())
    write_result(result, code)
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
