# Live Groq and Docker acceptance

Status: planned.

Pass PostgreSQL/SQS/Redis/Docker/Terraform checks and execute a Groq-generated allowlisted plan with the real PostgreSQL task store and SQS broker.

The user authorized starting local Docker services and using Groq. Preserve existing Compose projects, data and ports; use an empty dedicated project for destructive acceptance scenarios. Use only GROQ_API_KEY_1..4 loaded silently from the root .env and openai/gpt-oss-20b after authenticated model preflight. Never write credentials, headers, raw prompts or model responses to evidence. Keep fake/replay deterministic and use no silent fallback.

Limits: free-plan only; one 128-token completion; maximum one key pass, transient-only retry, bounded backoff/Retry-After. Only the designated free allowance is authorized; billed cost is PENDING absent billing evidence. Pause generation on quota/budget failures. A failed completed semantic evaluation is retained; do not repeat it merely for a passing sample.

Acceptance: offline checks pass, configured local service checks execute, the project-relevant live case records real model/usage/assertions, and artifacts include commands, exit codes and sanitized results. Missing prerequisites remain INCOMPLETE. Do not change the kit, publish, push, or perform real refunds/outbound messages.
