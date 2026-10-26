"""Evaluate a real Groq workflow over PostgreSQL and LocalStack SQS."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import boto3
import psycopg
from run_live_groq_eval import (
    MODEL,
    available_model_keys,
    load_credentials,
    request_plan,
)

from supportops_async.live_groq import GroqWorkflowRunner, validate_plan
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore
from supportops_async.worker import Worker

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = {
        "provider": "groq",
        "model": MODEL,
        "status": "INCOMPLETE",
        "cost_usd": "PENDING",
        "started_at_utc": datetime.now(UTC).isoformat(),
    }
    queues = []
    client = None
    try:
        if os.getenv("LLM_MODE", "fake") != "live":
            raise ValueError("explicit LLM_MODE=live required")
        keys = available_model_keys(load_credentials())
        result["model_available_key_count"] = len(keys)
        if not keys:
            raise RuntimeError("requested model unavailable")
        plan_response = request_plan(keys)
        plan = validate_plan(plan_response.choices[0].message.content or "")
        dsn = os.environ["P04_POSTGRES_DSN"]
        store = PostgresTaskStore(dsn)
        client = boto3.client(
            "sqs",
            endpoint_url=os.environ["P04_LOCALSTACK_ENDPOINT"],
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        for suffix in ("main", "dead"):
            queues.append(
                client.create_queue(QueueName=f"live-{suffix}-{uuid4().hex}")[
                    "QueueUrl"
                ]
            )
        broker = SqsBroker(client, *queues)
        task, _ = store.create(
            {
                "steps": plan,
                "request": "I received the dispatch message; where can I track the parcel?",
            },
            "live-" + uuid4().hex,
        )
        runner = GroqWorkflowRunner(
            keys, (ROOT / "agent/prompts/live-workflow.md").read_text(encoding="utf-8")
        )
        broker.publish(BrokerMessage(task.task_id))
        worker = Worker(store, broker, runner=runner)
        worker.run_once()
        completed = store.get(task.task_id)
        calls = runner.calls
        broker.publish(BrokerMessage(task.task_id))
        worker.run_once()
        with psycopg.connect(dsn) as connection:
            effect_count = connection.execute(
                "SELECT count(*) FROM effects WHERE task_id=%s", (task.task_id,)
            ).fetchone()[0]
        usage = plan_response.usage
        estimate = (
            runner.estimated_cost_usd
            + (usage.prompt_tokens * 0.075 + usage.completion_tokens * 0.30) / 1_000_000
        )
        checks = {
            "actual_model": plan_response.model == MODEL
            and runner.actual_model == MODEL,
            "completed": completed.status.value == "done",
            "effect_per_step": effect_count == len(plan),
            "all_steps_real": calls == len(plan),
            "duplicate_did_not_regenerate": runner.calls == calls,
            "within_budget": estimate <= 0.01,
        }
        result.update(
            status="PASS" if all(checks.values()) else "FAIL",
            assertions=checks,
            steps=plan,
            effect_count=effect_count,
            api_calls=1 + runner.calls,
            input_tokens=usage.prompt_tokens + runner.input_tokens,
            output_tokens=usage.completion_tokens + runner.output_tokens,
            estimated_cost_usd=estimate,
        )
    except Exception as exc:
        result["error"] = {
            "class": type(exc).__name__,
            "status": getattr(exc, "status_code", None),
        }
    finally:
        if client is not None:
            for queue in queues:
                client.delete_queue(QueueUrl=queue)
    code = 0 if result["status"] == "PASS" else 1
    result.update(exit_code=code, finished_at_utc=datetime.now(UTC).isoformat())
    folder = ROOT / "artifacts/evidence/live-docker"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (folder / f"groq-service-{stamp}.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
