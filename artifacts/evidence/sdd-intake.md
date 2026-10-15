# P04 intake and SDD evidence

- Command: `python -c "import json,pathlib,yaml; json.loads(pathlib.Path('docs/harness/sources.lock.json').read_text()); assert all((pathlib.Path('.planning/phases')/p/n).is_file() for p in ['001-api-store','002-broker-worker','003-durability','004-infrastructure'] for n in ['SPEC.md','PLAN.md','VERIFY.md']); print('P04 intake/SDD structure: PASS')"`
- Exit code: `0`
- Output: `P04 intake/SDD structure: PASS`
- Plan review: accepted before product code; 4 phases with 3–4 tasks each, owned paths, forbidden changes, validation, and stop conditions.
