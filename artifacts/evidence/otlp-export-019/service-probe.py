import json
import time
import urllib.error
import urllib.request

from pathlib import Path

attempt_marker = Path(__file__).with_name("service-probe-attempted.json")
if attempt_marker.exists():
    raise SystemExit("service probe is one-shot; prior attempt is recorded")
attempt_marker.write_text(
    json.dumps(
        {
            "candidate_commit": "d6cf5c9039e5dfd746331fda3f192e66e6e67184",
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "task_id": "ac52c679-8226-4658-9eca-6739e4caf906",
        },
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
traceparent = f"00-{trace_id}-00f067aa0ba902b7-01"
base = "http://127.0.0.1:18001"
request = urllib.request.Request(
    base + "/tasks",
    data=json.dumps({"payload": {"case": "otlp-smoke-019"}, "steps": ["synthetic-check"]}).encode(),
    headers={"Content-Type": "application/json", "Idempotency-Key": "otlp-smoke-019", "traceparent": traceparent},
    method="POST",
)
with urllib.request.urlopen(request, timeout=10) as response:
    created = json.load(response)
task_id = created["task_id"]
status = "unknown"
for _ in range(40):
    with urllib.request.urlopen(base + "/tasks/" + task_id, timeout=5) as response:
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
        with urllib.request.urlopen("http://127.0.0.1:24190/api/traces/" + trace_id, timeout=5) as response:
            trace = json.load(response)
        if trace.get("data"):
            break
    except (urllib.error.URLError, TimeoutError):
        pass
    time.sleep(0.5)
if not trace or not trace.get("data"):
    raise SystemExit("Jaeger did not return the deterministic trace")
spans = trace["data"][0].get("spans", [])
operations = sorted({span.get("operationName", "") for span in spans})
service_names = sorted({service.get("serviceName", "") for service in trace["data"][0].get("processes", {}).values()})
if "supportops.api.request" not in operations:
    raise SystemExit(f"API span missing; operations={operations}")
if not any("worker" in name.lower() for name in operations):
    raise SystemExit(f"worker span missing; operations={operations}")
if any(span.get("traceID") != trace_id for span in spans):
    raise SystemExit("returned span trace ID mismatch")
print(json.dumps({"task_id": task_id, "task_status": status, "trace_id": trace_id, "span_count": len(spans), "operations": operations, "service_names": service_names}, sort_keys=True))
