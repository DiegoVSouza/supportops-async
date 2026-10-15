# Verify — Broker and worker

- [x] Duplicate delivery produces one effect and two safe acknowledgements (in-memory broker unit test).
- [x] Notification consumer ignores duplicate `event_id` values and rejects malformed/unsupported event contracts (in-memory inbox unit test).
- [x] Transient failure retries with bounded delay; permanent failure reaches DLQ after N attempts (unit tests).
- [ ] SQS/SNS contract passes against LocalStack or remains INCOMPLETE with command evidence.
- [x] Unit and integration results are reported separately under `artifacts/evidence/`; LocalStack integration remains INCOMPLETE.
