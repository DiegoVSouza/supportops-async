from decimal import Decimal

import pytest

from scripts.campaign_ledger import CampaignLedger
from scripts.local_operation import CASE, LazySession, OperationBlocked, execute, reserve


def test_fake_default_never_reserves_or_accesses_services(monkeypatch):
    monkeypatch.setenv("LLM_MODE","fake")
    with pytest.raises(OperationBlocked,match="explicit_live"):
        execute()


def test_workflow_reservation_is_finite_and_duplicate_never_reopens(tmp_path):
    path=tmp_path/"ledger.sqlite"
    ledger=reserve(path)
    assert ledger.totals()["requests"]==3
    assert ledger.totals()["input_tokens"]==12288
    with pytest.raises(OperationBlocked,match="no_replay"):
        reserve(path)
    ledger.complete(case_id=CASE,trial=1,input_tokens=200,output_tokens=40,
                    actual_cost_usd=Decimal("0.000027"),outcome="ok",error_class=None)
    with pytest.raises(OperationBlocked,match="no_replay"):
        reserve(path)
    assert CampaignLedger(path,campaign_id="local-operation-v1").totals()["requests"]==3


def test_lazy_session_starts_once_and_binds_real_campaign():
    calls=[]
    class Session:
        def preview(self,envelope):
            assert envelope["campaign_id"]=="local-operation-v1"
        def complete(self,envelope):
            assert envelope["campaign_id"]=="local-operation-v1"
            calls.append(envelope["call_index"])
            return {"status":"ok"}
    factories=[]
    def factory():
        factories.append(1)
        return Session()
    session=LazySession(factory)
    assert factories==[]
    for index in (1,2):
        envelope={"campaign_id":"fixture-worker-v1","call_index":index}
        session.preview(envelope)
        session.complete(envelope)
    assert factories==[1] and calls==[1,2]


@pytest.mark.parametrize("calls",[True,0,4,1.5])
def test_workflow_reservation_rejects_invalid_call_counts(tmp_path,calls):
    from scripts.campaign_ledger import CampaignBlocked
    ledger=CampaignLedger(tmp_path/"ledger.sqlite",campaign_id="fixture")
    with pytest.raises(CampaignBlocked):
        ledger.reserve(case_id="fixture",trial=1,calls=calls,input_tokens=4096,output_tokens=512,
                       estimated_cost_usd=Decimal("0.0004608"),caps={"requests":6,"input_tokens":24576,
                       "output_tokens":3072,"estimated_cost_usd":Decimal("0.0027648")})
