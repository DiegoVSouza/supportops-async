# Verify — API-to-worker trace propagation and safe failures

Status: PLANNED. Save commands, exits, and sanitized outputs in `artifacts/evidence/api-worker-trace-propagation/`.

- [ ] API extracts only valid W3C traceparent and propagates no baggage or arbitrary headers.
- [ ] SQS/Redis/in-memory carriers preserve traceparent through serialization, retry/defer, redelivery, and DLQ; old context-free messages remain valid.
- [ ] Worker context is extracted and reaches threaded step execution; interruption recovery resumes remaining steps without repeating committed effects and keeps correlation context.
- [ ] New exception text is absent from task error state/API responses/outbox and worker logs; fixed failure codes and ERROR span status remain visible.
- [ ] Focused locked tests, fast gate, and offline full gate pass; Docker/Terraform/service gates are explicitly INCOMPLETE.
- [ ] All pre-existing artifacts, datasets/rubrics/campaign ledgers, and service configuration are byte-identical after validation.
- [ ] No credentials, provider, external network, Docker daemon, service, or external effect was accessed.
- [ ] Staged diff paths, whitespace, and secret scan pass; local commits are atomic.
- [ ] No RAG or service trace-export readiness is claimed. RAG source/protocol and exporter/bridge remain INCOMPLETE; human/independent review remains PENDING.
