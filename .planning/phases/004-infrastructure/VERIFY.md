# Verify — Infrastructure and CI

- [x] Compose configuration validates; service health and startup remain INCOMPLETE while the Docker daemon is unavailable.
- [ ] Docker image builds as non-root; no image push occurs. Build remains INCOMPLETE because the Docker daemon is unavailable.
- [ ] Terraform validate/plan completes without cloud credentials, otherwise INCOMPLETE. Terraform CLI and provider lock are unavailable.
- [x] CI commands match local fake-mode unit verification; bilingual docs contain no unsupported metrics. CI itself was not run on a remote provider.
- [x] Versioned local wheel has source commit/hash lock and isolated offline wheel install smoke; full dependency resolution offline remains INCOMPLETE because `psycopg-binary` is not available to the uv offline resolver.
