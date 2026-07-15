# Technical Debt Registry

Repository stabilization baseline completed.
Technical debt remains and is documented.

## Categories
- **Production blockers**
  - Production calibration evidence missing.
  - Real staging/prod deployment evidence missing.
- **Intentional placeholders**
  - Enterprise governance and observability stack placeholders.
  - Kubernetes baselines require environment adaptation; the values-only Helm placeholder has no templates and is not deployable.
- **Non-blocking polish**
  - Frontend lint-in-build currently warns about missing ESLint package in build phase.
  - Accessibility certification and full E2E coverage pending.

## TODO/FIXME audit summary
- No critical `TODO/FIXME/HACK` markers found in runtime code paths during this pass.
- Template docs intentionally include `TEMPLATE` markers and are retained as roadmap scaffolding.
