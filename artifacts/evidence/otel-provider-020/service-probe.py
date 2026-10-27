import json
import time
import urllib.error
import urllib.request
from pathlib import Path

marker = Path(__file__).with_name("service-probe-attempted.json")
if marker.exists():
    raise SystemExit("phase 020 service probe is one-shot; attempt marker exists")
trace_id = "a18b72e4c9634d1f9a2b6c5d0e8f4712"
task_id = None
marker.write_text(json.dumps({"candidate_commit": "beff749202805b138d820daaddb80a4468afc7c9", "trace_id": trace_id, "idempotency_key": "otel-provider-smoke-020", "attempted": True}, sort_keys=True) + "\n", encoding="utf-8")
request = urllib.request.Request(
    "http://127.0.0.1:18002/tasks",
    data=json.dumps({"payload": {"case": "otel-provider-smoke-020"}, "steps": ["synthetic-check"]}).encode(),
    headers={"Content-Type": "application/json", "Idempotency-Key": "otel-provider-smoke-020", "traceparent": f"00-{trace_id}-00f067aa0ba902b7-01"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=10) as response:
    task_id = json.load(response)["task_id"]
status = "unknown"
for _ in range(40):
    with urllib.request.urlopen("http://127.0.0.1:18002/tasks/" + task_id, timeout=5) as response:
        task = json.load(response)
    status = task.get("status")
    if status in {"completed", "failed", "done"}:
        break
    time.sleep(0.5)
if status not in {"completed", "done"}:
    raise SystemExit(f"synthetic task did not complete; status={status}")
trace = None
for _ in range(20):
    try:
        with urllib.request.urlopen("http://127.0.0.1:24191/api/traces/" + trace_id, timeout=5) as response:
            trace = json.load(response)
        if trace.get("data"):
            break
    except (urllib.error.URLError, TimeoutError):
        pass
    time.sleep(0.5)
if not trace or not trace.get("data"):
    raise SystemExit("Jaeger did not return the new deterministic trace")
data = trace["data"][0]
spans = data.get("spans", [])
operations = sorted({span.get("operationName", "") for span in spans})
service_names = sorted({service.get("serviceName", "") for service in data.get("processes", {}).values()})
allowed = {"supportops.http.method", "supportops.http.status_code", "supportops.worker.attempt", "supportops.error.category"}
attribute_keys = sorted({key for span in spans for key in span.get("tags", []) if key.get("key")})
observed_keys = {entry["key"] for entry in attribute_keys}
if observed_keys - allowed:
    raise SystemExit(f"non-allowlisted span attribute keys: {sorted(observed_keys - allowed)}")
if "supportops.api.request" not in operations or not any("worker" in name.lower() for name in operations):
    raise SystemExit(f"required API/worker spans missing; operations={operations}")
if any(span.get("traceID") != trace_id for span in spans):
    raise SystemExit("returned span trace ID mismatch")
if not {"supportops-async-api", "supportops-async-worker"}.issubset(set(service_names)):
    raise SystemExit(f"service resource attribution incomplete; service_names={service_names}")
print(json.dumps({"task_id": task_id, "task_status": status, "trace_id": trace_id, "span_count": len(spans), "operations": operations, "service_names": service_names, "attribute_keys": sorted(observed_keys)}, sort_keys=True))
