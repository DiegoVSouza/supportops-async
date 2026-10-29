# Verification

PASS accounted fixture API/Worker contract: four focused tests, attempt 1 exit 0. Duplicate API delivery produced exactly two accounted step calls and one effect per step; cancellation dispatched none; timeout became permanent failure/DLQ with no nack/retry and durable restart/new-ID block. Nonfixture sessions and extra payload data are rejected before reservation.

Locked check_full offline gate: 89 passed, four service skips, no failed checks; exit 2 INCOMPLETE. Docker daemon access was deliberately disabled for this phase (not an actual host outage), service endpoints were unconfigured, and Terraform CLI was absent. Compose config and fast gate passed; PostgreSQL/LocalStack/Redis/build/Terraform service acceptance remains pending. Full command/cwd/exit/output and explicit offline scope saved in artifacts/evidence/accounted-worker-029/full-offline-attempt1.json; focused evidence in focused-attempt1.json. No real provider/credentials/Docker lifecycle or Terraform apply.

Phase scope PASS_LOCAL_FIXTURE; full service and accounted live activation/funding/manifest/quality/review remain INCOMPLETE/PENDING. Implementer self-assessment only. No failure counter consumed by the intentionally unavailable service gates.
