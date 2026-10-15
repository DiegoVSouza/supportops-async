# Verify - Phase 007: LocalStack queue initialization

## Required checks
1. Validate the READY hook creates both queues and its RedrivePolicy against LocalStack.
2. Run service integration tests for PostgreSQL idempotency and SQS publish/consume/visibility/ack.
3. Build and start the API and worker images; verify service health and non-root user.
4. Run the full P04 gate. Record Terraform availability and leave validate/plan INCOMPLETE if the CLI is absent.
5. Record exact commands, exit codes, and output under artifacts/evidence/.

## Results
- Pending execution.
