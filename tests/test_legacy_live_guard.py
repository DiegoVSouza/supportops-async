import importlib
import sys
import types
from pathlib import Path

import pytest


def test_legacy_entries_stop_before_provider_or_services(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    monkeypatch.setitem(sys.modules, "groq", types.SimpleNamespace(Groq=object))
    groq = importlib.import_module("run_live_groq_eval")
    service = importlib.import_module("run_live_service_eval")

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected external access")

    for module in (groq, service):
        monkeypatch.setattr(module, "load_credentials", forbidden)
        monkeypatch.setattr(module, "request_plan", forbidden)
    monkeypatch.setattr(service.boto3, "client", forbidden)
    assert groq.main() == 2
    assert service.main() == 2


def test_default_runtime_provider_construction_is_denied():
    from supportops_async.live_groq import GroqWorkflowRunner

    with pytest.raises(RuntimeError, match="accounted_guard_required"):
        GroqWorkflowRunner._new_client("synthetic-test-only")
