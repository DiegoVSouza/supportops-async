# Verify — Broker and worker

- [ ] Duplicate delivery produces one effect and two safe acknowledgements.
- [ ] Notification consumer ignores duplicate `event_id` values and rejects malformed/unsupported event contracts.
- [ ] Transient failure retries with bounded delay; permanent failure reaches DLQ after N attempts.
- [ ] SQS/SNS contract passes against LocalStack or remains INCOMPLETE with command evidence.
- [ ] Unit and integration results are reported separately under `artifacts/evidence/`.
