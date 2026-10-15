from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .models import Task, TaskStatus
from .sqlite import InvalidTransition


class PostgresTaskStore:
    """PostgreSQL implementation of the task contract (DSN supplied by caller)."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        with psycopg.connect(dsn) as conn:
            from pathlib import Path
            conn.execute((Path(__file__).parent / "migrations" / "001_tasks.sql").read_text())

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _task(row: dict[str, Any] | None) -> Task | None:
        if row is None:
            return None
        payload = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
        result = row["result"] if isinstance(row["result"], (dict, type(None))) else json.loads(row["result"])
        return Task(row["task_id"], TaskStatus(row["status"]), payload, row["step"], row["progress"], result, row["error"], row["attempts"])

    def create(self, payload: dict[str, Any], idem_key: str) -> tuple[Task, bool]:
        if not idem_key.strip() or len(idem_key) > 200:
            raise ValueError("Idempotency-Key must contain 1 to 200 characters")
        task_id = str(uuid.uuid4())
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            conn.execute("INSERT INTO tasks(task_id,status,payload) VALUES(%s,%s,%s::jsonb)", (task_id, "queued", self._dump(payload)))
            inserted = conn.execute("INSERT INTO idempotency(idem_key,task_id) VALUES(%s,%s) ON CONFLICT(idem_key) DO NOTHING", (idem_key, task_id)).rowcount
            if inserted:
                conn.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(%s,%s,%s,%s::jsonb)", (str(uuid.uuid4()), "task.created", task_id, self._dump({"task_id": task_id, "status": "queued"})))
                return self._task(conn.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,)).fetchone()), True  # type: ignore[return-value]
            conn.execute("DELETE FROM tasks WHERE task_id=%s", (task_id,))
            row = conn.execute("SELECT t.* FROM idempotency i JOIN tasks t USING(task_id) WHERE i.idem_key=%s", (idem_key,)).fetchone()
            if row is None:
                # UUID collision is vanishingly unlikely; retry explicitly rather than misreporting conflict.
                raise RuntimeError("task ID collision")
            return self._task(row), False  # type: ignore[return-value]

    def get(self, task_id: str) -> Task | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            return self._task(conn.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,)).fetchone())

    def claim(self, task_id: str, worker_id: str) -> bool:
        with psycopg.connect(self.dsn) as conn:
            return conn.execute("UPDATE tasks SET status='running',worker_id=%s,lease_until=now()+interval '30 seconds',attempts=attempts+1 WHERE task_id=%s AND (status IN ('queued','retrying') OR (status='running' AND lease_until<=now()))", (worker_id, task_id)).rowcount == 1

    def heartbeat(self, task_id: str, worker_id: str) -> bool:
        with psycopg.connect(self.dsn) as conn:
            return conn.execute("UPDATE tasks SET lease_until=now()+interval '30 seconds' WHERE task_id=%s AND worker_id=%s AND status='running'", (task_id, worker_id)).rowcount == 1

    def checkpoint(self, task_id: str, step: str, state: dict[str, Any]) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute("INSERT INTO checkpoints(task_id,step,state) VALUES(%s,%s,%s::jsonb) ON CONFLICT(task_id,step) DO UPDATE SET state=EXCLUDED.state", (task_id, step, self._dump(state)))
            conn.execute("UPDATE tasks SET step=%s,progress=GREATEST(progress,%s) WHERE task_id=%s AND status='running'", (step, SQLiteStepNumber(step), task_id))

    def effect(self, task_id: str, step: str) -> dict[str, Any] | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            row = conn.execute("SELECT result FROM effects WHERE task_id=%s AND step=%s", (task_id, step)).fetchone()
            return row["result"] if row else None

    def apply_effect(self, task_id: str, step: str, result: dict[str, Any]) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            prior = conn.execute("SELECT result FROM effects WHERE task_id=%s AND step=%s", (task_id, step)).fetchone()
            if prior:
                return prior["result"]
            conn.execute("INSERT INTO effects(task_id,step,result) VALUES(%s,%s,%s::jsonb)", (task_id, step, self._dump(result)))
            conn.execute("INSERT INTO checkpoints(task_id,step,state) VALUES(%s,%s,%s::jsonb) ON CONFLICT(task_id,step) DO UPDATE SET state=EXCLUDED.state", (task_id, step, self._dump(result)))
            conn.execute("UPDATE tasks SET step=%s,progress=GREATEST(progress,%s) WHERE task_id=%s AND status='running'", (step, SQLiteStepNumber(step), task_id))
            return result

    def complete(self, task_id: str, result: dict[str, Any]) -> None:
        self._transition(task_id, "done", result=result)

    def fail(self, task_id: str, error: str) -> None:
        self._transition(task_id, "failed", error=error[:1000])

    def retry(self, task_id: str) -> None:
        self._transition(task_id, "retrying")

    def cancel(self, task_id: str) -> bool:
        with psycopg.connect(self.dsn) as conn:
            return conn.execute("UPDATE tasks SET status='cancelled' WHERE task_id=%s AND status IN ('queued','retrying','running')", (task_id,)).rowcount == 1

    def enqueue_event(self, event_type: str, task_id: str, payload: dict[str, Any]) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(%s,%s,%s,%s::jsonb)", (str(uuid.uuid4()), event_type, task_id, self._dump(payload)))

    def pending_events(self) -> list[tuple[str, str, dict[str, Any]]]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute("SELECT event_id,event_type,payload FROM event_outbox WHERE sent_at IS NULL ORDER BY created_at,event_id").fetchall()
            return [(row["event_id"], row["event_type"], row["payload"]) for row in rows]

    def mark_event_sent(self, event_id: str) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute("UPDATE event_outbox SET sent_at=now() WHERE event_id=%s AND sent_at IS NULL", (event_id,))

    def _transition(self, task_id: str, status: str, *, result: dict[str, Any] | None = None, error: str | None = None) -> None:
        with psycopg.connect(self.dsn) as conn:
            changed = conn.execute("UPDATE tasks SET status=%s,result=%s::jsonb,error=%s WHERE task_id=%s AND status NOT IN ('done','failed','cancelled')", (status, self._dump(result) if result is not None else None, error, task_id)).rowcount
            if not changed:
                row = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
                if row is None:
                    raise KeyError(task_id)
                raise InvalidTransition(f"task is already {row[0]}")
            event_type = {"done": "task.completed", "failed": "task.failed"}.get(status)
            if event_type:
                payload = {"task_id": task_id, "status": status, "result": result} if result is not None else {"task_id": task_id, "status": status, "error": error}
                conn.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(%s,%s,%s,%s::jsonb)", (str(uuid.uuid4()), event_type, task_id, self._dump(payload)))


def SQLiteStepNumber(step: str) -> int:
    try:
        return int(step.split(":", 1)[0])
    except ValueError:
        return 0
