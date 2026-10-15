import asyncio

import httpx

from supportops_async.api import create_app
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore


def test_create_replay_status_cancel_and_not_found():
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    app = create_app(store, broker)
    body = {"payload": {"ticket": "T-1"}, "steps": ["triage"]}
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            first = await client.post("/tasks", json=body, headers={"Idempotency-Key": "abc"})
            replay = await client.post("/tasks", json=body, headers={"Idempotency-Key": "abc"})
            assert first.status_code == 202
            assert replay.json() == first.json()
            assert replay.headers["Idempotency-Replayed"] == "true"
            task_id = first.json()["task_id"]
            assert (await client.get(f"/tasks/{task_id}")).json()["status"] == "queued"
            assert (await client.post(f"/tasks/{task_id}/cancel")).json()["status"] == "cancelled"
            assert (await client.post(f"/tasks/{task_id}/cancel")).status_code == 409
            assert (await client.get("/tasks/missing")).status_code == 404
    asyncio.run(scenario())


def test_contract_rejects_missing_key_extra_fields_and_bad_steps():
    app = create_app(SQLiteTaskStore(), InMemoryBroker())
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.post("/tasks", json={})).status_code == 400
            assert (await client.post("/tasks", json={"unexpected": True}, headers={"Idempotency-Key": "x"})).status_code == 422
            assert (await client.post("/tasks", json={"steps": []}, headers={"Idempotency-Key": "x"})).status_code == 422
    asyncio.run(scenario())
