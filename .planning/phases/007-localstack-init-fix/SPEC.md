# Spec - Phase 007: LocalStack queue initialization

## Trigger
The P04 service test against the running Docker PostgreSQL and LocalStack services passed PostgreSQL idempotency but failed SQS because the READY hook creates the DLQ and then passes RedrivePolicy using invalid AWS CLI shorthand.

## Acceptance
- The LocalStack READY hook creates the configured source queue with a valid RedrivePolicy and the DLQ.
- Re-running the service integration test proves PostgreSQL idempotency and SQS publish/consume/visibility/ack against the isolated local Docker stack.
- Compose image build, runtime health, and non-root image configuration are checked when supported.
- Evidence records each command, exit code, and output. The full gate remains INCOMPLETE for any service or Terraform check that cannot be executed.
- No AWS deployment, Terraform apply, publication, or external action occurs.
