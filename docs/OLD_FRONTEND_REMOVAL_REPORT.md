# Old Frontend Removal Report

Date: 2026-06-29

## 1. Executive summary

A repository-wide sweep was performed for the Reflex cutover and legacy Next.js removal decision. Reflex is present, route-registered, lint-clean, type-clean, tested, and exportable after repairing a Reflex theme merge-conflict syntax error and missing shared layout/style primitives. However, destructive deletion gates did **not** pass because the root repository test suite, root lint target, docs truthfulness check, Docker verification, and stale active Next.js/deployment references still have blockers.

## 2. Removal decision

**Decision: do not delete `frontend/` in this PR.**

The old frontend remains intact because critical deletion gates failed. This is a blocker report, not a physical archive/removal PR.

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
- Reflex lint, type check, test suite, and export pass after the fixes in this PR.
- Backend route source inspection confirms the required public API routes and Trace API routes exist, including the requested policy-facts endpoint.
- FastAPI/Jinja Market DTO routes exist for `/web/market-time-machine`, `/web/timeline`, `/web/candle/{candle_id}`, and `/web/evidence/{packet_id}`.

## 5. Gates failed

- `python -m pytest -q` failed: 22 failures remain in MCP async plugin handling, object-storage docs/runtime expectations, an integration string-contract check for Reflex route literals, Citadel assessment persistence, Market health fake DB handling, and model/migration parity.
- `make lint` failed on existing E402 imports in `tests/storage/test_storage_health.py`.
- `make docs-truthfulness` failed because docs are missing market-time-machine API routes and exported domain models.
- `docker compose config` could not run because `docker` is not installed in this environment.
- Legacy Next.js references remain in README, docs, CI, deploy/runtime profiles, `.env.example`, and Makefile material, so no-docs-active-Next.js and no-production-route-depends-on-Next.js gates cannot be claimed.
- Root repository forbidden-wording audit still finds the configured phrases in safety-denylist test fixtures and the retained legacy `frontend/`; because `frontend/` was not removed, this remains documented rather than silently deleted.

## 6. Files/directories removed

None. `frontend/` was deliberately left intact.

## 7. Files modified

- `reflex_frontend/bastion_ui/theme/tokens.py`
- `reflex_frontend/bastion_ui/theme/styles.py`
- `reflex_frontend/bastion_ui/components/layout/container.py`
- `docs/OLD_FRONTEND_REMOVAL_REPORT.md`
- Documentation status files updated for this non-deletion decision.

## 8. Routes now owned by Reflex

Reflex is verified as the primary migration frontend for:

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

- Active legacy references still direct some docs, CI, env examples, and deployment profiles to Next.js or rollback behavior.
- The root integration contract expects literal `route="/check"` strings in `app.py`, while some routes are registered through `PUBLIC_ROUTE_SPECS`.
- Docker and deployment verification require a Docker-enabled environment.
- Formal browser/accessibility evidence was not generated in this non-interactive sweep.

## 11. Safety/no-custody verification

No custody behavior was added. The verified Reflex copy and validators preserve advisory-only behavior, public Bitcoin address-only input, no legal-verification wording, no Bitcoin consensus-proof wording, no seed/private-key/wallet-file/signing-material collection, and visible degraded/limited-evidence states.

## 12. Configured wording audit

The repository-wide configured wording scan was run. Matches remain in denylist tests and retained legacy frontend files. Because deletion gates failed, `frontend/` was not removed and these matches are documented as blockers/fixtures rather than treated as a passing removal state.

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

- `python -m pytest -q` failed with 22 failures.
- `make lint` failed with E402 errors in `tests/storage/test_storage_health.py`.
- `make docs-truthfulness` failed with missing API/model documentation coverage.
- `docker compose config` failed because Docker is not installed.

## 16. Commands skipped and why

- `make runtime-render-compose`, `make runtime-render-k3s`, and `make runtime-render-k8s` were not run after Docker/root blockers were found; the destructive deletion path had already failed and runtime rendering should be re-run in the follow-up config cleanup PR.
- Live browser screenshots were not taken because no runnable web server/browser verification was requested after the non-deletion decision and the changes were repair/configuration oriented.

## 17. Rollback limitations after deletion

No deletion occurred, so rollback remains unchanged: `frontend/` is still available. If a future PR deletes `frontend/`, rollback will require restoring it from Git history or a tagged archive and reintroducing any Next.js-specific CI/deployment configuration removed in that future PR.

## 18. Final recommendation

Do **not** delete the legacy Next.js frontend yet. First fix the root test/lint/docs-truthfulness failures, remove or reclassify active Next.js references across docs/CI/deploy/runtime config, verify Docker/runtime rendering in a Docker-enabled environment, and then run a dedicated destructive removal PR.
