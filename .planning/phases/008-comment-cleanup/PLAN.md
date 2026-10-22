# Plan

LLM_MODE: fake

allowed_write_paths: `.planning/phases/008-comment-cleanup/`, `supportops_async/store/postgres.py`, `artifacts/evidence/comment-cleanup*.txt`.

1. Remove redundant comments while retaining safety rationale.
2. Run the fast check and compare the Python token stream; save results.

Forbidden: behavior, interface, prompt, dependency, or tool changes. Stop on a failed check.
