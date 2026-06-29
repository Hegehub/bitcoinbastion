# Reflex Frontend Cutover Status

## Decision

Current decision: **controlled partial cutover complete; physical Next.js archive blocked**.

Reflex remains the preferred primary frontend in runtime profile metadata. Next.js remains in `frontend/` as the rollback frontend. FastAPI/Jinja Market routes remain delegated where documented.

## Cutover checklist

| Gate | Status | Notes |
| --- | --- | --- |
| Reflex route parity | PASS | Required public, Trace, and Console routes are implemented and tested. |
| Reflex API parity | PASS/PARTIAL | Public and Trace endpoint parity passes; Market detail routes remain delegated. |
| Trace migration | PASS | Safety/no-custody and API checks pass for migration-primary use. |
| Market migration | PARTIAL / DELEGATED | Reflex preview routes exist; FastAPI/Jinja remains canonical for detail/fallback. |
| Console migration | BASELINE PASS | Modules exist as read-only/operator preview surfaces. |
| Safety/no-custody | PASS | No custody or wallet-secret input path introduced. |
| Forbidden wording | PASS | Repository scanner passes after final docs avoid blocked wording outside allowlists. |
| Accessibility/responsive | PARTIAL | Baseline exists; formal manual audit remains required. |
| Reflex build/export | PASS | Local Reflex sync/lint/typecheck/tests/export passed. |
| Legacy rollback build | PASS | Next.js install/lint/typecheck/tests/build passed. |
| Root backend suite | FAIL/PARTIAL | Known non-Reflex/root-suite failures remain. |
| Docker local build | BLOCKED | Docker unavailable in this agent environment; CI wiring exists. |
| Next.js archive | BLOCKED | Keep as legacy rollback. |

## What changed in the controlled cutover

- Runtime metadata prefers Reflex in `reflex` and `parallel` frontend modes.
- Environment examples expose `BASTION_PRIMARY_FRONTEND=reflex` and `BASTION_LEGACY_FRONTEND=nextjs`.
- Rollback documentation explains how to return to Next.js and keep FastAPI/Jinja Market routes.

## What did not change

- `frontend/` was not deleted or moved.
- FastAPI/Jinja Market routes were not removed.
- Backend domain logic was not moved into Reflex.
- No custody, signing, wallet-secret, mining, or Stratum capability was introduced.
- Production readiness is not claimed.

## Remaining cutover blockers

1. Resolve or scope root-suite async/plugin and legacy root Reflex contract failures.
2. Run Docker build on a host or CI runner with Docker available.
3. Complete a formal accessibility/responsive/manual browser audit.
4. Decide whether Market detail routes stay delegated permanently or receive full Reflex parity.
5. Keep Next.js available until maintainers approve a separate archive PR.

## Final destructive cleanup gate (2026-06-28)

Decision: **blocked; keep `frontend/` intact**.

The full cutover audit in `docs/FRONTEND_REFLEX_FULL_CUTOVER_AUDIT.md` confirms that Reflex remains the preferred primary migration frontend, but the old Next.js frontend cannot be deleted yet. The blockers are the failing root test suite, Docker verification being unavailable in this agent environment, Market detail/drill-down delegation, active rollback references in deployment/docs/CI material, and incomplete formal accessibility/manual browser evidence.

No runnable frontend was removed in this pass.

## Old frontend removal sweep update (2026-06-29)

Decision remains **blocked; keep `frontend/` intact**. Reflex is verified as the preferred primary migration frontend locally, Trace remains Reflex-owned for migration purposes, and Market remains partial/delegated to FastAPI/Jinja for detail/dashboard routes. See `docs/OLD_FRONTEND_REMOVAL_REPORT.md`.

## Reflex-only frontend removal update (2026-06-29)

Maintainer requested removal of the old frontend. `frontend/` and the legacy frontend CI/parallel compose support have been deleted. Reflex remains the only frontend in the working tree; Market detail/dashboard routes remain delegated to FastAPI/Jinja.
