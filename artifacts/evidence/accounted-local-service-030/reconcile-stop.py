"""Conservatively finalize one incomplete workflow, retaining all three calls."""
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root))
from scripts.campaign_ledger import CampaignLedger

base=root/"artifacts/evals/live"
with closing(sqlite3.connect((base/"provider-usage.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
    assert db.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]==2
    rows=db.execute("SELECT event,status,actual_input,actual_output FROM usage_events ORDER BY sequence").fetchall()
    assert rows==[("reserved",None,None,None),("completed","ok",105,51)]
with closing(sqlite3.connect((base/"operations.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
    assert db.execute("SELECT operation,step,status FROM attempts").fetchall()==[("fixture-local-01","triage","reserved")]
ledger=CampaignLedger(base/"ledger.sqlite",campaign_id="local-operation-v1")
assert len(ledger.reserved_trials())==1
ledger.complete(case_id="fixture-local-01",trial=1,input_tokens=None,output_tokens=None,
                actual_cost_usd=None,outcome="incomplete",error_class="unknown")
totals=ledger.totals()
assert totals["requests"]==3 and totals["input_tokens"]==12288 and totals["output_tokens"]==1536
report={"status":"PASS_CONSERVATIVE_RECONCILIATION","workflow_result":"INCOMPLETE","provider_calls":1,
        "observed_input_tokens":105,"observed_output_tokens":51,"logical_calls_retained":3,
        "logical_input_tokens_retained":12288,"logical_output_tokens_retained":1536,
        "actual_billed_usd":None,"provider_accessed":False,"replay_allowed":False,
        "cause":"original_failure_category_not_preserved"}
(Path(__file__).resolve().parent/"stop-reconciled.json").write_text(json.dumps(report,indent=2)+"\n",newline="\n")
print(json.dumps(report))
