# Next.js Frontend Archive Record

Audit date: 2026-06-28
Removal status: **NOT REMOVED**

## 1. Why Next.js was not removed

The destructive deletion gate did not pass. The legacy Next.js frontend remains in `frontend/` because root-suite verification is failing, Docker verification could not run in this environment, Market detail routes remain delegated to FastAPI/Jinja, and rollback references remain intentionally active in deployment/docs/CI material.

## 2. Last known role of Next.js

Next.js is a legacy rollback frontend. It is not the preferred migration frontend, but it remains runnable while Reflex stabilizes and while maintainers retain a rollback path.

## 3. Reflex replacement path

The replacement frontend lives in `reflex_frontend/`. Reflex owns the preferred public, Trace, Console, and Market preview surfaces. FastAPI remains the backend source of truth.

## 4. Final verification summary

- Reflex sync, lint, typecheck, tests, and export passed in the final migration verification cycle.
- Legacy Next.js install, lint, typecheck, tests, and build passed in the final migration verification cycle.
- Root `python -m pytest -q` failed with known non-Reflex/root-suite failures.
- Docker checks were blocked by missing Docker access in the agent environment.
- Safety/no-custody and blocked-wording scanners passed.

## 5. Last known blockers

1. Root suite must be fixed or explicitly scoped before destructive cleanup.
2. Docker build/config checks must pass on a Docker-capable host or CI runner.
3. Market detail delegation must be accepted as permanent or migrated to Reflex.
4. Active rollback references must be removed only after maintainers approve losing the runnable fallback.
5. Formal accessibility/manual browser evidence remains incomplete.

## 6. How to recover from git history if removal happens later

If a future PR removes `frontend/`, recover it from the last commit before that removal with:

```bash
git checkout <pre-removal-commit> -- frontend
```

Then rerun the legacy verification commands documented in the rollback plan before using it operationally.

## 7. Date of removal

Not applicable. The frontend was kept on 2026-06-28 because the deletion gate was blocked.
