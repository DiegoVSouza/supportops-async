# Plan

1. Verify cached Terraform and LocalStack image identities, an empty phase namespace and baseline Docker state; use a fresh copy of the P04 Terraform configuration and cached provider under phase evidence.
2. Start a phase-owned LocalStack and run locked Terraform init, validate and plan-only from an isolated container on its network; record exit codes and sanitized output.
3. Remove only phase-owned resources and reconcile existing identities and states; report this as a scoped Terraform gate, not a full product or exporter acceptance.

allowed_write_paths: `.planning/phases/023-local-terraform-network/**`, `artifacts/evidence/local-terraform-network-023/**`, `docs/harness/progress.md`. forbidden_changes: product source, existing Terraform files/state, historical evidence, other Docker resources, images/tags, provider/model calls, real credentials, apply, external deployment, gateway and approvals.

Mode fake, paid budget USD 0, no provider model calls. Use only cached images, fake LocalStack credentials, local network, finite process timeouts and no public listener. Stop on unavailable cached provider, namespace collision, external requests, nonlocal endpoint or command failure. Capture baseline and final Docker identities/states. Plan-check is self-assessment; independent review PENDING. This is a Docker-local test network, not a host/provider bridge.
