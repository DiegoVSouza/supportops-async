from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from supportops_async.live_groq import GroqWorkflowRunner


@pytest.mark.parametrize(
    "content", ['{"reply":"wrong key"}', '{"response":""}', '"plain text"']
)
def test_draft_rejects_output_outside_the_step_schema(content):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8),
    )
    runner = GroqWorkflowRunner(
        ["test-credential"],
        "Synthetic policy.",
        client_factory=Mock(return_value=client),
    )
    with pytest.raises(ValueError, match="step contract"):
        runner({}, "draft_reply")
    assert runner.calls == 1
    assert client.chat.completions.create.call_count == 1


def test_worker_callable_uses_provider_json_and_reports_usage():
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content='{"category":"shipping"}'))
        ],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8),
    )
    runner = GroqWorkflowRunner(
        ["test-credential"],
        "Synthetic tracking policy.",
        client_factory=Mock(return_value=client),
    )
    assert runner({}, "triage") == {"category": "shipping"}
    assert runner.calls == 1 and runner.input_tokens == 20
    assert (
        client.chat.completions.create.call_args.kwargs["model"] == "openai/gpt-oss-20b"
    )


def test_worker_callable_rejects_unallowlisted_steps_before_network():
    factory = Mock(side_effect=AssertionError("network must not run"))
    runner = GroqWorkflowRunner(
        ["test-credential"], "Synthetic policy.", client_factory=factory
    )
    with pytest.raises(ValueError, match="step"):
        runner({}, "refund")
    factory.assert_not_called()


def test_duplicate_delivery_reuses_the_committed_provider_result():
    from supportops_async.queue.contracts import BrokerMessage
    from supportops_async.queue.memory import InMemoryBroker
    from supportops_async.store.sqlite import SQLiteTaskStore
    from supportops_async.worker import Worker

    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content='{"category":"shipping"}'))
        ],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8),
    )
    runner = GroqWorkflowRunner(
        ["test-credential"],
        "Synthetic policy.",
        client_factory=Mock(return_value=client),
    )
    store, broker = SQLiteTaskStore(), InMemoryBroker()
    task, _ = store.create({"steps": ["triage"]}, "live-duplicate")
    broker.publish(BrokerMessage(task.task_id))
    broker.publish(BrokerMessage(task.task_id))
    worker = Worker(store, broker, runner=runner)
    assert worker.run_once() and worker.run_once()
    assert store.get(task.task_id).status.value == "done"
    assert runner.calls == 1


def test_budget_preflight_blocks_before_the_provider():
    factory = Mock(side_effect=AssertionError("network must not run"))
    runner = GroqWorkflowRunner(
        ["test-credential"],
        "Synthetic policy.",
        client_factory=factory,
        budget_usd=0.000000001,
    )
    with pytest.raises(RuntimeError, match="budget preflight"):
        runner({}, "triage")
    factory.assert_not_called()


def test_only_transient_provider_errors_rotate(monkeypatch):
    error = RuntimeError("fixture")
    error.status_code = 503
    first, second = Mock(), Mock()
    first.chat.completions.create.side_effect = error
    second.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content='{"category":"shipping"}'))
        ],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8),
    )
    monkeypatch.setattr("supportops_async.live_groq.time.sleep", lambda _: None)
    factory = Mock(side_effect=[first, second])
    runner = GroqWorkflowRunner(
        ["first", "second"], "Synthetic policy.", client_factory=factory
    )
    assert runner({}, "triage")["category"] == "shipping"
    assert runner.attempts == 2
    error.status_code = 401
    factory = Mock(return_value=first)
    with pytest.raises(RuntimeError, match="provider failure"):
        GroqWorkflowRunner(
            ["first", "second"], "Synthetic policy.", client_factory=factory
        )({}, "triage")
    assert factory.call_count == 1
