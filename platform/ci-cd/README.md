# CI/CD

Owns GitHub Actions workflows, release gates, build verification, deployment automation and evidence-producing checks.

Current canonical paths:

- `.github/workflows/`
- `Makefile`
- `scripts/`
- release/evidence documentation under `docs/`

Migration rule: CI/CD changes must keep reproducibility, deterministic gates and explicit release evidence as first-class outputs.
