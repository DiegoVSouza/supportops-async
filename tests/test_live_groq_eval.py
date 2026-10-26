import json
import pytest
from supportops_async.live_groq import validate_plan

@pytest.mark.parametrize("value",['{"steps":["triage","draft_reply"]}','{"steps":["triage"]}'])
def test_validate_plan_accepts_only_bounded_local_steps(value):
    assert validate_plan(value)[0]=="triage"

@pytest.mark.parametrize("value",['bad json','{"steps":["refund"]}','{"steps":["draft_reply","triage"]}','{"steps":["triage","triage"]}','{"steps":[]}'])
def test_validate_plan_fails_closed(value):
    with pytest.raises(ValueError): validate_plan(value)
