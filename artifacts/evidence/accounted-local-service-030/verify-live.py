"""Read-only receipt and OTLP service verification of the existing operation."""
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
result=json.loads((out/"live-result.json").read_text())
assert result["status"]=="ok" and result["provider_calls"]==2 and result["telemetry_flushed"]
with closing(sqlite3.connect((root/"artifacts/evals/live/provider-usage.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
    rows=db.execute("SELECT attempt_id,actual_input,actual_output FROM usage_events WHERE event='completed' AND status='ok'").fetchall()
assert len(rows)==2 and {r[0] for r in rows}==set(result["receipts"])
assert sum(r[1] for r in rows)==result["input_tokens"] and sum(r[2] for r in rows)==result["output_tokens"]
data=None
for attempt in range(5):
    with urlopen("http://127.0.0.1:35486/api/traces/"+result["trace_id"],timeout=5) as response:
        data=json.load(response)
    if data.get("data"):
        break
    time.sleep(.5)
spans=data["data"][0]["spans"]
names={s["operationName"] for s in spans}
assert {"supportops.api.request","supportops.worker.process","supportops.llm.accounted"} <= names
assert all(s["traceID"]==result["trace_id"] for s in spans)
llm=[s for s in spans if s["operationName"]=="supportops.llm.accounted"]
assert len(llm)==2
for span in spans:
    assert not span.get("logs")
    for tag in span["tags"]:
        assert "content" not in tag["key"] and "description" not in tag["key"]
        assert "fixture-local-01" not in str(tag["value"])
        assert not any(receipt in str(tag["value"]) for receipt in result["receipts"])
assert sum(next(t["value"] for t in s["tags"] if t["key"]=="supportops.llm.input_tokens") for s in llm)==result["input_tokens"]
report={"status":"PASS","provider_calls":2,"input_tokens":result["input_tokens"],"output_tokens":result["output_tokens"],
        "receipt_matches":True,"correlated_api_worker_llm":True,"content_exported":False,"trace_id":result["trace_id"],
        "reserved_workflow_calls":3,"operating_envelope":6,"actual_billed_usd":None}
(out/"reconciliation.json").write_text(json.dumps(report,indent=2)+"\n",newline="\n")
print(json.dumps(report))
