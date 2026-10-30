# Specification

Replace the P04 revalidation wrapper's misleading process-only credential check with a safe root `.env`/process preflight. The result must expose only slot names and booleans, must preserve the explicit-live, authority, manifest, reservation and no-replay guards, and must not call a provider. This phase cannot dispatch operation032 or refresh its stale manifest.
