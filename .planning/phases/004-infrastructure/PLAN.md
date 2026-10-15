# Plan — Infrastructure and CI

## allowed_write_paths
- `infra/**`, `docker-compose.async.yml`, `Dockerfile*`, `.github/workflows/**`, `scripts/**`
- `supportops_async/api/runtime.py`, `supportops_async/worker/cli.py`, `.env.example`, `.dockerignore`, `.gitignore`
- `artifacts/**`, `docs/**`, `README*`, `pyproject.toml`, `uv.lock`

## forbidden_changes
No deployment, image push, cloud credentials, or unreviewed Terraform apply.

## Tasks
1. Add non-root multi-stage worker/API images and local compose dependencies.
2. Add Terraform SQS/SNS/IAM minimum and run validate/plan only with local/mock config.
3. Add CI for unit tests, integration profile, and Docker build without push.
4. Add executable local runtime/event outbox wiring and document recovery demo, states, delivery semantics, and limitations EN/PT-BR.

## Check and stop
Run locally available checks; unavailable Docker/Terraform/LocalStack gates are INCOMPLETE with evidence.
