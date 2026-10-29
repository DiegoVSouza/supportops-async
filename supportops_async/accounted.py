"""Durable fixture-accounted runner for the real API/worker contract."""
import json
import re
import sqlite3
from contextlib import closing

from supportops_async.worker.runner import PermanentFailure

MODEL = "openai/gpt-oss-20b"
STEPS = ("triage", "draft_reply")


class AccountedWorkflowRunner:
    def __init__(self, path, session):
        if getattr(session, "provenance", None) != "fixture":
            raise PermanentFailure("fixture_session_required")
        self.path, self.session = path, session

    def __call__(self, payload, step):
        operation = payload.get("operation_id") if isinstance(payload, dict) else None
        if (not isinstance(operation, str) or not re.fullmatch(r"fixture-[A-Za-z0-9_-]{1,48}", operation)
                or step not in STEPS or set(payload) - {"operation_id", "steps"}
                or payload.get("steps") != list(STEPS)):
            raise PermanentFailure("synthetic_contract")
        field = "category" if step == "triage" else "response"
        envelope = {"campaign_id": "fixture-worker-v1", "case_id": operation, "trial": 1,
                    "call_index": STEPS.index(step) + 1, "timeout_seconds": 20,
                    "payload": {"model": MODEL, "messages": [
                        {"role": "system", "content": "Return only a JSON object with a nonempty string field: " + field},
                        {"role": "user", "content": "Synthetic shipping ticket: where can I find the tracking link? No real action is authorized."}],
                        "max_completion_tokens": 512, "temperature": 0,
                        "reasoning_effort": "low", "include_reasoning": False}}
        with closing(sqlite3.connect(self.path, timeout=5)) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS attempts(operation TEXT, step TEXT,status TEXT NOT NULL,receipt TEXT,input_tokens INTEGER,output_tokens INTEGER,PRIMARY KEY(operation,step))")
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM attempts WHERE status!='ok'").fetchone():
                raise PermanentFailure("prior_work_requires_review")
            if db.execute("SELECT 1 FROM attempts WHERE operation=? AND step=?", (operation, step)).fetchone():
                raise PermanentFailure("already_reserved")
            if db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= 4:
                raise PermanentFailure("fixture_allocation_exhausted")
            db.execute("INSERT INTO attempts(operation,step,status) VALUES (?,?,'reserved')", (operation, step))
            db.commit()
        try:
            self.session.preview(envelope)
            result = self.session.complete(envelope)
        except Exception:
            raise PermanentFailure("uncertain_accounted_attempt") from None
        usage = result.get("usage") if isinstance(result, dict) else None
        if (not isinstance(result, dict) or result.get("status") != "ok" or result.get("model") != MODEL
                or not isinstance(result.get("attempt_id"), str)
                or not re.fullmatch(r"[0-9a-f]{32}", result["attempt_id"])
                or not isinstance(usage, dict)
                or any(type(usage.get(key)) is not int or not 0 <= usage[key] <= cap
                       for key, cap in (("input_tokens", 4096), ("output_tokens", 512)))):
            raise PermanentFailure("invalid_accounted_receipt")
        try:
            output = json.loads(result.get("content", ""))
            if (not isinstance(output, dict) or set(output) != {field}
                    or not isinstance(output[field], str) or not 1 <= len(output[field]) <= 1000
                    or not output[field].strip()):
                raise ValueError()
            if step == "triage" and output[field] not in {"shipping", "billing", "technical", "other"}:
                raise ValueError()
        except (ValueError, TypeError):
            raise PermanentFailure("step_contract") from None
        with closing(sqlite3.connect(self.path, timeout=5)) as db:
            db.execute("PRAGMA synchronous=FULL")
            if db.execute("SELECT 1 FROM attempts WHERE receipt=?", (result["attempt_id"],)).fetchone():
                raise PermanentFailure("duplicate_receipt")
            db.execute("UPDATE attempts SET status='ok',receipt=?,input_tokens=?,output_tokens=? WHERE operation=? AND step=? AND status='reserved'",
                       (result["attempt_id"], usage["input_tokens"], usage["output_tokens"], operation, step))
            db.commit()
        return output
