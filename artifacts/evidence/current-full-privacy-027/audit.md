# Current full gate execution record

Source candidate before verification: 5e08bd6 (phase 026 OTLP HTTP wire privacy). No product source was changed in this phase. Scope is actual API/worker serialized failure spans plus the existing full local fake gate, not production telemetry or live model quality.

Preflight first failed on absent Docker Health fields before lifecycle. The corrected snapshot reads only optional safe state/project fields. Second preflight found occupied host ports 24566/26379 (listener PID 31584); no phase resource was started. Planned ports were amended to 35432/34566/36379 and verified by bind before startup. No existing listener was modified.

First full gate failed: pytest CLI could not import scripts without project PYTHONPATH, and internal Docker networking prevented the Windows host PostgreSQL probe. Terraform still produced a local plan, but that did not pass the failed gate. Phase-owned cleanup succeeded; exact container/network/volume identities and old images matched. Unique image supportops-async:phase027 was retained. This FAIL is preserved in full-attempt1-attempt3.txt and reconciliation.json.

Correction reuses phase025's ordinary bridge plus explicit LocalStack service DNS and loopback ports; it does not introduce or infer a host gateway. PYTHONPATH is explicitly the project root for the existing pytest entrypoint. A fresh pytest directory and fresh Terraform workspace preserve the first attempt. Full gate attempt 2 is recorded separately. No test assertion was weakened. Existing phase023's anonymous volume remains present in all baseline/reconciliation inventories and is not attributed or removed.

Real RAG is still INCOMPLETE: current supportops_async/shared source search finds no owned corpus, retrieval contract or trusted tenant/source protocol. Implementing a new source would require those inputs; fixture/golden data and sibling code cannot supply them. Quality, human/independent review, production exporter/backend identity, canary and promotion remain pending.
