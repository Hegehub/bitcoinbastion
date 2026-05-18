# Mypy Closure Plan

Last updated: 2026-05-18

## Current status
- `make lint`: **PASS** (`python -m ruff check app tests`, `python -m mypy app`).
- Repository-wide `mypy` gate is currently green on the tracked release branch.

## Remaining typed-debt scope (intentionally temporary overrides)
The following modules are still listed in `pyproject.toml` `[[tool.mypy.overrides]]` with `ignore_errors = true`:
- `app.services.citadel.disaster_simulation_service`
- `app.services.treasury.treasury_service`
- `app.services.citadel.citadel_assessment_service`
- `app.services.citadel.repair_plan_service`
- `app.services.observability.operations_service`
- `app.services.delivery.publish_service`

## Closure sequence
1. Remove override for low-count modules first (smallest error clusters).
2. Fix medium modules with strict typed boundary models (TypedDict/Pydantic schemas) at service/repository edges.
3. Fix `citadel_assessment_service` last as the largest cluster.
4. After each module closure:
   - run `python -m mypy app/<module_path>.py` using a temporary config with no overrides,
   - run `make lint`,
   - remove module from override list only after passing.

## Guardrails
- Keep global `strict = true`.
- Do not remove `mypy` from `make lint`.
- Avoid blanket `Any` and broad `type: ignore` suppression.
- Prefer narrow guards, explicit conversions, and schema validation for stable payload shapes.

## RC truth note
Mypy gate is no longer the release blocker. Current blocker for full PRODUCTION RELEASE CANDIDATE declaration is **target-environment evidence attachment**, not repository lint status.
