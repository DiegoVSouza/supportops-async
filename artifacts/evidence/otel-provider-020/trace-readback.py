import json
import re
import urllib.request

trace_id = "a18b72e4c9634d1f9a2b6c5d0e8f4712"
with urllib.request.urlopen("http://127.0.0.1:24191/api/traces/" + trace_id, timeout=5) as response:
    trace = json.load(response)
if not trace.get("data"):
    raise SystemExit("Jaeger has no stored trace for the already completed task")
data = trace["data"][0]
spans = data.get("spans", [])
operations = sorted({span.get("operationName", "") for span in spans})
service_names = sorted({service.get("serviceName", "") for service in data.get("processes", {}).values()})
allowed = {
    "supportops.http.method", "supportops.http.status_code", "supportops.worker.attempt", "supportops.error.category",
    "code.function.name", "http.request.method", "http.response.status_code", "http.route",
    "network.protocol.version", "otel.scope.name", "otel.scope.version", "server.address",
    "server.port", "span.kind", "url.path", "url.scheme",
}
tags = [tag for span in spans for tag in span.get("tags", []) if isinstance(tag, dict) and isinstance(tag.get("key"), str)]
observed = {tag["key"] for tag in tags}
if observed - allowed:
    raise SystemExit(f"non-allowlisted span attribute keys: {sorted(observed - allowed)}")
bad_types = sorted({tag["key"] for tag in tags if not isinstance(tag.get("value"), (str, int, float, bool))})
if bad_types:
    raise SystemExit(f"span attributes with non-scalar values: {bad_types}")
expected_types = {
    "supportops.http.method": str,
    "supportops.http.status_code": int,
    "supportops.worker.attempt": int,
    "supportops.error.category": str,
    "code.function.name": str,
    "http.request.method": str,
    "http.response.status_code": int,
    "http.route": str,
    "network.protocol.version": str,
    "otel.scope.name": str,
    "otel.scope.version": str,
    "server.address": str,
    "server.port": int,
    "span.kind": str,
    "url.path": str,
    "url.scheme": str,
}
wrong_types = sorted({tag["key"] for tag in tags if tag["key"] in expected_types and type(tag["value"]) is not expected_types[tag["key"]]})
long_values = sorted({tag["key"] for tag in tags if isinstance(tag.get("value"), str) and (len(tag["value"]) > 256 or any(ord(char) < 32 for char in tag["value"]))})
if wrong_types or long_values:
    raise SystemExit(f"span attribute type/bound check failed; wrong_types={wrong_types}; long_or_controlled={long_values}")
uuid_in_values = any(
    isinstance(tag.get("value"), str)
    and re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}", tag["value"])
    for tag in tags
)
if uuid_in_values:
    raise SystemExit("span attribute contains a UUID-shaped value")
if "supportops.api.request" not in operations or not any("worker" in name.lower() for name in operations):
    raise SystemExit(f"required API/worker spans missing; operations={operations}")
if any(span.get("traceID") != trace_id for span in spans):
    raise SystemExit("returned span trace ID mismatch")
if not {"supportops-async-api", "supportops-async-worker"}.issubset(set(service_names)):
    raise SystemExit(f"service resource attribution incomplete; service_names={service_names}")
print(json.dumps({"task_id": "d05d93a4-22a7-4d5d-a773-89b854cc0d7e", "task_status": "done", "trace_id": trace_id, "span_count": len(spans), "operations": operations, "service_names": service_names, "attribute_keys": sorted(observed), "attribute_values_scalar_bounded_and_uuid_free": True}, sort_keys=True))
