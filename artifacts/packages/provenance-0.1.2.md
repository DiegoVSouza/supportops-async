# P04 local wheel provenance

- Distribution: `supportops-async` version `0.1.2`.
- Artifact: `supportops_async-0.1.2-py3-none-any.whl`.
- Source commit: `3aa96ec9d3fa2f85f771d9b5aaa4c5ab3641034d` (`build(p04): prepare async package 0.1.2`).
- SHA-256: `a41c2a5a6c797e3913a510321d6859b5ab3be73b3f796eb7e9b1ea76fe6f5fd8`.
- Dependency lock SHA-256: `1a43601d07f101deadad1563b8cc8cefbadb6733c38127b43e81850189440fcc`.
- Build: `uv build --offline --out-dir artifacts/packages .`; exit 0; output is `artifacts/evidence/p04-012-wheel-build.txt`.
- Consumer: installed with `python -m pip install --no-index --no-deps --target artifacts/tmp/p04-012-site2 ...`; isolated `python -I -S scripts/package_smoke.py` loaded the wheel outside the source checkout, verified FastAPI 0.142.4 and migration inclusion, and completed a fake task. Both commands exited 0; see `artifacts/evidence/p04-012-wheel-install.txt` and `p04-012-wheel-consumer.txt`.
- The wheel is local and has not been published. The artifact lock is verified by `scripts/verify_artifact_lock.py`.
