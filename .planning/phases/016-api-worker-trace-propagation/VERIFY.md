# Verify — API-to-worker trace propagation and safe failures

Status: OFFLINE CONTROL PASS; EXTERNAL SERVICE / TRACE EXPORT / RAG INCOMPLETE; HUMAN AND INDEPENDENT REVIEW PENDING. Commands, exits, sanitized outputs, and protected-state hashes are in `artifacts/evidence/api-worker-trace-propagation/`.

- [x] API extracts valid W3C traceparent and propagates no baggage or arbitrary headers; invalid and overlong carriers are discarded.
- [x] SQS/Redis/in-memory carriers preserve traceparent through serialization, retry/defer, redelivery, and DLQ; old context-free messages remain valid.
- [x] Worker context reaches threaded step execution; recovery resumes remaining steps without repeating committed effects and keeps correlation context.
- [x] New exception text is absent from task error state/outbox and worker CLI logs; fixed failure categories and ERROR status are set on spans.
- [x] Focused locked tests passed (20); fast gate and artifact lock checks passed; full offline gate passed tests (67) and reported four service skips, Compose config PASS, Docker build/PostgreSQL/LocalStack/Terraform INCOMPLETE.
- [x] 157 protected tracked artifact/eval/config files remained byte-identical. Existing ignored pytest temporary files were restored byte-for-byte (3 files).
- [x] No credentials, provider, external service, Docker daemon, or external effect was accessed; no outbound network was needed. Docker CLI parsed Compose config, but daemon access used a nonexistent named pipe.
- [x] Phase 016 staged paths match the plan; `git diff --check` is clean; secret scan of the staged delta found no credential assignment or secret value. Local implementation commit is created after review.
- [x] No RAG or service trace-export readiness is claimed. RAG source/protocol and exporter/bridge remain INCOMPLETE; human/independent review remains PENDING.
