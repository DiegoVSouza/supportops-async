# Verify - Phase 007: LocalStack queue initialization

## Required checks
1. Validate the READY hook creates both queues, redrive policy, and topics in LocalStack.
2. Run service integration tests for PostgreSQL idempotency and SQS publish/consume/visibility/ack.
3. Build and start the P04 API and worker images; verify health and non-root user.
4. Run Terraform init, validate, and a non-applying plan against LocalStack using host CLI or the official Docker image.
5. Run the P04 full gate with configured service endpoints. Record exact commands, exit codes, and outputs under artifacts/evidence/.

## Results
- [x] 1 PASS: LocalStack 4.14.0 READY hook created task and DLQ queues plus SNS topics. Fix uses AWS CLI 1.44.45 JSON file input for RedrivePolicy.
- [x] 2 PASS_SERVICE: PostgreSQL idempotency and LocalStack SQS publish/consume/visibility/ack passed twice; see phase-007-service-tests-repeat-1.txt and phase-007-service-tests-repeat-2.txt. Full suite with service endpoints: 29 passed, see phase-007-full-tests.txt.
- [x] 3 PASS_DOCKER: Compose config and image build passed; API/worker task was persisted as done; both processes run as UID 10001. See phase-007-check-full.txt and phase-007-docker-demo.txt.
- [x] 4 PASS_LOCAL_PLAN: Terraform 1.16.6 init, validate, and plan passed through the official Docker image; plan reports 6 to add, 0 to change, 0 to destroy. No apply. See phase-007-check-full.txt.
- [x] 5 PASS: python scripts/check_full.py returned exit 0 with services configured; output in phase-007-check-full.txt.
- [ ] 6 INCOMPLETE: long-step lease renewal, crash recovery, retries, and DLQ have not been exercised as a service-backed failure scenario; unit/local tests remain separate.
- [ ] 7 PENDING: live model quality/cost are not measured.

The host-only integration-test command exited 0 on both repeats. The local API/worker demonstration used fake mode. Docker image pulls were limited to pinned project dependencies and the official Terraform CLI image. No cloud apply or publication occurred.
