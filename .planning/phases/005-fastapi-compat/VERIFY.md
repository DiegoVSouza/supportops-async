# Verify — FastAPI consumer compatibility

- [ ] FastAPI 0.142.4 imports with the locked supported dependencies.
- [ ] API contract and all available unit/recovery tests pass on FastAPI 0.142.4.
- [ ] `pyproject.toml`, `uv.lock`, source record, and ADR agree on supported FastAPI versions and transitive telemetry dependency.
- [ ] Package version is the next patch and wheel metadata expresses the supported FastAPI range.
- [ ] Wheel hash, source commit, lock hash, isolated install, and behavior smoke are recorded.
- [ ] No P05 files or sibling imports were used or changed.
