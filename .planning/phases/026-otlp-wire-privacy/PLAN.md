# Plan

1. Add a bounded loopback collector regression exercising actual API and worker failure spans through the locked OTLP exporter; retain only sanitized assertions.
2. Run focused tests, fast and full offline fake gate and record commands and outputs. Preserve existing artifacts and report service dependencies accurately.

allowed_write_paths: `.planning/phases/026-otlp-wire-privacy/**`, `tests/test_otlp_wire_privacy.py`, `artifacts/evidence/otlp-wire-privacy-026/**`, `docs/harness/progress.md`. forbidden_changes: production source, historical evidence, provider calls, real data, external services, other projects and approvals. Fake mode, USD 0, no model calls. Stop on non-loopback binding, raw sentinel leakage in artifacts, failed tests or unexpected service effects. Plan-check self-assessment; independent review PENDING.
