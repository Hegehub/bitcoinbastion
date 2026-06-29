# Old Frontend Removal Report

Date: 2026-06-29

## 1. Executive summary

The legacy Next.js frontend has been removed from this branch at maintainer request. Reflex remains as the only repository-native frontend under `reflex_frontend/`. The sweep preserved the no-custody posture and did not add seed phrase, private key, wallet-file, signing, Stratum/mining, or distributed-backend behavior.

This report does not claim broad production readiness: root-suite, lint, docs-truthfulness, and Docker checks still have blockers that must be fixed in follow-up work.

## 2. Removal decision

**Decision: delete `frontend/` and keep Reflex.**

Maintainer instruction superseded the prior non-deletion decision. Rollback now requires restoring `frontend/` from Git history or a tagged archive.

## 3. Gates checked

- Repository syntax/import/lint/test sweep.
- Reflex app existence, app name, ports, route registration, dynamic route syntax, tests, and export.
- Reflex API client base URL, `ResponseEnvelope.data` unwrapping, timeout/error handling, and degraded-state handling.
- Backend public, Trace, and FastAPI/Jinja Market route availability by source inspection.
- Trace no-custody and sensitive-material rejection by source/test inspection.
- Market ownership/delegation.
- Configured wording audit.
- Legacy Next.js reference audit.
- Docker/runtime config verification.
- Docs truthfulness verification.

## 4. Gates passed

- Reflex app exists under `reflex_frontend/`.
- `rxconfig.py` uses `app_name="bastion_ui"`, frontend port `3001`, and backend port `8001`.
- Required public routes are registered by `PUBLIC_ROUTE_SPECS` and dynamic Trace routes use Reflex bracket syntax.
- Required console routes are registered in the Reflex app.
- Required Market routes are registered as Reflex preview routes while FastAPI/Jinja remains the delegated detail/dashboard surface.
- Reflex API client uses configured backend base URL, unwraps `data`, and normalizes HTTP errors/timeouts/transport failures.
- Reflex safety code rejects seed phrases, mnemonic-like input, private keys, xprv/yprv/zprv/tprv material, `wallet.dat`, keystore JSON-like content, WIF-like material, and signing material.
- Reflex lint, type check, test suite, and export pass after the theme/layout repairs.
- Backend route source inspection confirms the required public API routes and Trace API routes exist, including the requested policy-facts endpoint.
- FastAPI/Jinja Market DTO routes exist for `/web/market-time-machine`, `/web/timeline`, `/web/candle/{candle_id}`, and `/web/evidence/{packet_id}`.

## 5. Gates failed or still blocked

- `python -m pytest -q` previously failed: 22 failures remained in MCP async plugin handling, object-storage docs/runtime expectations, an integration string-contract check for Reflex route literals, Citadel assessment persistence, Market health fake DB handling, and model/migration parity.
- `make lint` previously failed on existing E402 imports in `tests/storage/test_storage_health.py`.
- `make docs-truthfulness` previously failed because docs were missing market-time-machine API routes and exported domain models.
- `docker compose config` could not run because `docker` is not installed in this environment.
- Historical docs still mention the old Next.js era; active runtime configuration has been updated to Reflex-only where touched in this PR.

## 6. Files/directories removed

- `frontend/`
- `.github/workflows/frontend-ci.yml`
- `deploy/compose/full-parallel-frontends.compose.yaml`

## 7. Files modified

- `.env.example`
- `Makefile`
- `README.md`
- `deploy/runtime-profiles/compose.yaml`
- `deploy/runtime-profiles/profiles.yaml`
- `docs/FRONTEND_REFLEX_CUTOVER_STATUS.md`
- `docs/FRONTEND_REFLEX_FINAL_AUDIT.md`
- `docs/FRONTEND_ROLLBACK_PLAN.md`
- `docs/NEXTJS_LEGACY_ARCHIVE_PLAN.md`
- `docs/OLD_FRONTEND_REMOVAL_REPORT.md`
- `docs/PRODUCTION_READINESS.md`
- `docs/STATUS.md`
- `reflex_frontend/README.md`
- `reflex_frontend/bastion_ui/components/layout/container.py`
- `reflex_frontend/bastion_ui/theme/styles.py`
- `reflex_frontend/bastion_ui/theme/tokens.py`

## 8. Routes now owned by Reflex

Reflex is the only repository-native frontend for:

- `/`
- `/platform`
- `/developers`
- `/operations`
- `/manifesto`
- `/evidence`
- `/status`
- `/roadmap`
- `/security`
- `/docs`
- `/check`
- `/trace`
- `/trace/[report_id]`
- `/trace/[report_id]/proof-packet`
- `/console`
- `/console/trace`
- `/console/evidence`
- `/console/market-intelligence`
- `/console/time-machine`
- `/console/sovereign-grid`
- `/console/policy`
- `/console/audit`

## 9. Routes delegated to FastAPI/Jinja

Market remains explicitly delegated/partial rather than exclusively Reflex-owned. FastAPI/Jinja continues to own detail/dashboard routes and DTO endpoints, including:

- `/market`
- `/market-time-machine`
- `/market/time-machine`
- `/market/{section}`
- `/intelligence/timeline`
- `/evidence/{packet_id}`
- `/candles/{candle_id}`
- `/web/market-time-machine`
- `/web/timeline`
- `/web/candle/{candle_id}`
- `/web/evidence/{packet_id}`

## 10. Remaining frontend risks

- Rollback is no longer runnable from the working tree; restoring the old frontend requires Git history.
- Some historical migration/audit documents still reference the old frontend for context.
- Docker and deployment verification require a Docker-enabled environment.
- Formal browser/accessibility evidence was not generated in this non-interactive sweep.

## 11. Safety/no-custody verification

No custody behavior was added. The verified Reflex copy and validators preserve advisory-only behavior, public Bitcoin address-only input, no legal-verification wording, no Bitcoin consensus-proof wording, no seed/private-key/wallet-file/signing-material collection, and visible degraded/limited-evidence states.

## 12. Configured wording audit

The repository-wide configured wording scan was run. After deleting `frontend/`, remaining matches are in denylist fixtures, scanner code, or historical/safety documentation contexts and should be handled by a dedicated docs hygiene PR if maintainers want a zero-match repository scan.

## 13. Commands run

- `python -m pytest -q`
- `make lint`
- `make docs-truthfulness`
- `cd reflex_frontend && uv sync && uv run ruff check . && uv run mypy bastion_ui && uv run pytest && uv run reflex export`
- `docker compose config`
- `rg -n "<configured forbidden address-morality phrases>" . || true`
- `rg -n "frontend/|Next\\.js|next\\.config|npm run|localhost:3000|NEXT_PUBLIC|framer-motion|tailwind.config|vitest|playwright" README.md docs Makefile deploy .github docker-compose* .env.example pyproject.toml 2>/dev/null || true`

## 14. Commands passed

- `cd reflex_frontend && uv sync`
- `cd reflex_frontend && uv run ruff check .`
- `cd reflex_frontend && uv run mypy bastion_ui`
- `cd reflex_frontend && uv run pytest`
- `cd reflex_frontend && uv run reflex export`

## 15. Commands failed

- `python -m pytest -q` failed with 22 failures before this deletion pass.
- `make lint` failed with E402 errors in `tests/storage/test_storage_health.py` before this deletion pass.
- `make docs-truthfulness` failed with missing API/model documentation coverage before this deletion pass.
- `docker compose config` failed because Docker is not installed.

## 16. Commands skipped and why

- `make runtime-render-compose`, `make runtime-render-k3s`, and `make runtime-render-k8s` were not run because Docker/runtime verification is unavailable in this environment and root verification blockers remain.
- Live browser screenshots were not taken because no server/browser verification was available in this non-interactive cleanup pass.

## 17. Rollback limitations after deletion

`frontend/` has been deleted. Rollback to the old frontend now requires restoring that directory and any removed workflow/compose definitions from Git history or a tagged archive. Runtime metadata has been updated so Reflex is the only active frontend mode in the working tree.

## 18. Final recommendation

Proceed with Reflex-only frontend development. Follow-up PRs should fix root test/lint/docs-truthfulness blockers, run Docker/runtime checks in a Docker-enabled environment, and clean historical migration documents that still describe the pre-deletion era.
