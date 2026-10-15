from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

from .models import TERMINAL, Task, TaskStatus


class InvalidTransition(ValueError):
    pass


class SQLiteTaskStore:
    """Transactional local store used by tests and the offline demo."""

    def __init__(self, path: str | Path = ":memory:", *, lease_seconds: float = 30.0) -> None:
        self.path = str(path)
        if lease_seconds < 0:
            raise ValueError("lease_seconds must be non-negative")
        self.lease_seconds = lease_seconds
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        if self.path != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL,
              step TEXT, progress INTEGER NOT NULL DEFAULT 0, result TEXT, error TEXT,
              attempts INTEGER NOT NULL DEFAULT 0, worker_id TEXT, lease_until REAL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS idempotency (idem_key TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(task_id));
            CREATE TABLE IF NOT EXISTS checkpoints (
              task_id TEXT NOT NULL REFERENCES tasks(task_id), step TEXT NOT NULL,
              state TEXT NOT NULL, PRIMARY KEY(task_id, step)
            );
            CREATE TABLE IF NOT EXISTS effects (
              task_id TEXT NOT NULL REFERENCES tasks(task_id), step TEXT NOT NULL,
              result TEXT NOT NULL, PRIMARY KEY(task_id, step)
            );
            CREATE TABLE IF NOT EXISTS event_outbox (
              event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, task_id TEXT NOT NULL,
              payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, sent_at TEXT
            );
            """
        )
        columns = {row["name"] for row in self._db.execute("PRAGMA table_info(tasks)")}
        if "lease_until" not in columns:
            self._db.execute("ALTER TABLE tasks ADD COLUMN lease_until REAL")

    def close(self) -> None:
        self._db.close()

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def _task(self, row: sqlite3.Row | None) -> Task | None:
        if row is None:
            return None
        return Task(row["task_id"], TaskStatus(row["status"]), json.loads(row["payload"]), row["step"], row["progress"], json.loads(row["result"]) if row["result"] else None, row["error"], row["attempts"])

    def create(self, payload: dict[str, Any], idem_key: str) -> tuple[Task, bool]:
        if not idem_key.strip() or len(idem_key) > 200:
            raise ValueError("Idempotency-Key must contain 1 to 200 characters")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                old = self._db.execute("SELECT task_id FROM idempotency WHERE idem_key=?", (idem_key,)).fetchone()
                if old:
                    task = self.get(old["task_id"])
                    self._db.commit()
                    return task, False  # type: ignore[return-value]
                task_id = str(uuid.uuid4())
                self._db.execute("INSERT INTO tasks(task_id,status,payload) VALUES(?,?,?)", (task_id, TaskStatus.QUEUED, self._dump(payload)))
                self._db.execute("INSERT INTO idempotency(idem_key,task_id) VALUES(?,?)", (idem_key, task_id))
                self._db.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(?,?,?,?)", (str(uuid.uuid4()), "task.created", task_id, self._dump({"task_id": task_id, "status": "queued"})))
                task = self.get(task_id)
                self._db.commit()
                return task, True  # type: ignore[return-value]
            except Exception:
                self._db.rollback()
                raise

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._task(self._db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone())

    def claim(self, task_id: str, worker_id: str) -> bool:
        with self._lock, self._db:
            cur = self._db.execute("UPDATE tasks SET status=?, worker_id=?, lease_until=julianday('now') + ? / 86400.0, attempts=attempts+1 WHERE task_id=? AND (status IN (?,?) OR (status=? AND lease_until <= julianday('now'))) ", (TaskStatus.RUNNING, worker_id, self.lease_seconds, task_id, TaskStatus.QUEUED, TaskStatus.RETRYING, TaskStatus.RUNNING))
            return cur.rowcount == 1

    def heartbeat(self, task_id: str, worker_id: str) -> bool:
        with self._lock, self._db:
            cur = self._db.execute("UPDATE tasks SET lease_until=julianday('now') + ? / 86400.0 WHERE task_id=? AND worker_id=? AND status=?", (self.lease_seconds, task_id, worker_id, TaskStatus.RUNNING))
            return cur.rowcount == 1

    def checkpoint(self, task_id: str, step: str, state: dict[str, Any]) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT INTO checkpoints(task_id,step,state) VALUES(?,?,?) ON CONFLICT(task_id,step) DO UPDATE SET state=excluded.state", (task_id, step, self._dump(state)))
            self._db.execute("UPDATE tasks SET step=?, progress=MAX(progress,?) WHERE task_id=? AND status=?", (step, self._step_number(step), task_id, TaskStatus.RUNNING))

    @staticmethod
    def _step_number(step: str) -> int:
        try:
            return int(step.split(":", 1)[0])
        except ValueError:
            return 0

    def effect(self, task_id: str, step: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute("SELECT result FROM effects WHERE task_id=? AND step=?", (task_id, step)).fetchone()
            return json.loads(row["result"]) if row else None

    def apply_effect(self, task_id: str, step: str, result: dict[str, Any]) -> dict[str, Any]:
        """Atomically record the simulated idempotent effect and its checkpoint."""
        with self._lock, self._db:
            prior = self._db.execute("SELECT result FROM effects WHERE task_id=? AND step=?", (task_id, step)).fetchone()
            if prior:
                return json.loads(prior["result"])
            encoded = self._dump(result)
            self._db.execute("INSERT INTO effects(task_id,step,result) VALUES(?,?,?)", (task_id, step, encoded))
            self._db.execute("INSERT INTO checkpoints(task_id,step,state) VALUES(?,?,?) ON CONFLICT(task_id,step) DO UPDATE SET state=excluded.state", (task_id, step, encoded))
            self._db.execute("UPDATE tasks SET step=?, progress=MAX(progress,?) WHERE task_id=? AND status=?", (step, self._step_number(step), task_id, TaskStatus.RUNNING))
            return result

    def complete(self, task_id: str, result: dict[str, Any]) -> None:
        self._transition(task_id, TaskStatus.DONE, result=result, event_type="task.completed")

    def fail(self, task_id: str, error: str) -> None:
        self._transition(task_id, TaskStatus.FAILED, error=error[:1000], event_type="task.failed")

    def retry(self, task_id: str) -> None:
        self._transition(task_id, TaskStatus.RETRYING)

    def cancel(self, task_id: str) -> bool:
        with self._lock, self._db:
            cur = self._db.execute("UPDATE tasks SET status=? WHERE task_id=? AND status IN (?,?,?)", (TaskStatus.CANCELLED, task_id, TaskStatus.QUEUED, TaskStatus.RETRYING, TaskStatus.RUNNING))
            return cur.rowcount == 1

    def enqueue_event(self, event_type: str, task_id: str, payload: dict[str, Any]) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(?,?,?,?)", (str(uuid.uuid4()), event_type, task_id, self._dump(payload)))

    def pending_events(self) -> list[tuple[str, str, dict[str, Any]]]:
        with self._lock:
            rows = self._db.execute("SELECT event_id,event_type,payload FROM event_outbox WHERE sent_at IS NULL ORDER BY created_at,event_id").fetchall()
            return [(row["event_id"], row["event_type"], json.loads(row["payload"])) for row in rows]

    def mark_event_sent(self, event_id: str) -> None:
        with self._lock, self._db:
            self._db.execute("UPDATE event_outbox SET sent_at=CURRENT_TIMESTAMP WHERE event_id=? AND sent_at IS NULL", (event_id,))

    def _transition(self, task_id: str, status: TaskStatus, *, result: dict[str, Any] | None = None, error: str | None = None, event_type: str | None = None) -> None:
        with self._lock, self._db:
            row = self._db.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            if TaskStatus(row["status"]) in TERMINAL:
                raise InvalidTransition(f"task is already {row['status']}")
            self._db.execute("UPDATE tasks SET status=?, result=?, error=? WHERE task_id=?", (status, self._dump(result) if result is not None else None, error, task_id))
            if event_type:
                payload = {"task_id": task_id, "status": status.value, "result": result} if result is not None else {"task_id": task_id, "status": status.value, "error": error}
                self._db.execute("INSERT INTO event_outbox(event_id,event_type,task_id,payload) VALUES(?,?,?,?)", (str(uuid.uuid4()), event_type, task_id, self._dump(payload)))
