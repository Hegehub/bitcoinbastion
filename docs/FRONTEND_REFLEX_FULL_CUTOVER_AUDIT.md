# Full Reflex Frontend Cutover Audit

Audit date: 2026-06-28

## 1. Executive summary

Deletion readiness decision: **BLOCKED — do not remove `frontend/` in this PR**.

Reflex is the preferred primary migration frontend for public, Trace, Console, and Market preview routes, but the destructive cleanup gate does not pass. The legacy Next.js frontend remains required as a rollback surface until the repository-root test suite is either fixed or explicitly scoped, Docker verification runs on a Docker-capable host, Market detail ownership is accepted as delegated or fully migrated, and active deployment/CI/docs references are converted away from rollback assumptions.

The final action for this prompt is therefore a rollback-safe audit: keep `frontend/`, document blockers, and avoid claiming that Reflex is the only frontend.

## 2. Current frontend ownership

| Surface | Current owner | Status | Notes |
| --- | --- | --- | --- |
| Public marketing and static routes | Reflex | PASS | Registered through `reflex_frontend/bastion_ui/routes/` and `app.py`. |
| Trace public flow | Reflex | PASS | `/check`, `/trace`, dynamic report, and proof-packet pages are registered. |
| Console/operator routes | Reflex | BASELINE PASS | Read-only/operator preview modules exist; several remain baseline surfaces rather than full production consoles. |
| Market preview routes | Reflex | PARTIAL | Reflex routes exist for dashboard, timeline, time-machine, signals, evidence, narratives, and sources. |
| Market detail/drill-down routes | FastAPI/Jinja | DELEGATED | `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}` remain canonical FastAPI/Jinja routes. |
| Legacy rollback frontend | Next.js in `frontend/` | REQUIRED | Deletion is blocked by verification and rollback gates. |

## 3. Reflex route parity status

| Route | Expected Owner | Actual Owner | Implementation Path | Status | Blocker |
| --- | --- | --- | --- | --- | --- |
| `/` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/home.py` | PASS | None |
| `/platform` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/platform.py` | PASS | None |
| `/developers` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/developers.py` | PASS | None |
| `/operations` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/operations.py` | PASS | None |
| `/manifesto` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/manifesto.py` | PASS | None |
| `/evidence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/evidence.py` | PASS | None |
| `/status` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/status.py` | PASS | None |
| `/roadmap` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/roadmap.py` | PASS | None |
| `/security` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/security.py` | PASS | None |
| `/docs` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/docs.py` | PASS | None |
| `/check` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/check.py` | PASS | None |
| `/trace` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/trace.py` | PASS | None |
| `/trace/[report_id]` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/trace_report.py` | PASS | None |
| `/trace/[report_id]/proof-packet` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/proof_packet.py` | PASS | None |
| `/console` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console.py` | BASELINE PASS | Baseline/operator-preview semantics remain documented. |
| `/console/trace` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_trace.py` | BASELINE PASS | Read-only preview. |
| `/console/evidence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_evidence.py` | BASELINE PASS | Read-only preview. |
| `/console/market-intelligence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_market_intelligence.py` | BASELINE PASS | Read-only preview. |
| `/console/time-machine` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_time_machine.py` | BASELINE PASS | Read-only preview. |
| `/console/sovereign-grid` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_sovereign_grid.py` | BASELINE PASS | Read-only preview. |
| `/console/policy` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_policy.py` | BASELINE PASS | Read-only preview. |
| `/console/audit` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_audit.py` | BASELINE PASS | Read-only preview. |
| `/market` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market.py` | PARTIAL | Detail drill-down remains delegated. |
| `/market/timeline` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_timeline.py` | PARTIAL | Backing detail data remains delegated. |
| `/market/time-machine` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_time_machine.py` | PARTIAL | Backing detail data remains delegated. |
| `/market/signals` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_signals.py` | PARTIAL | Backing detail data remains delegated. |
| `/market/evidence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_evidence.py` | PARTIAL | `/evidence/{packet_id}` remains delegated. |
| `/market/narratives` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_narratives.py` | PARTIAL | Narrative detail ownership remains delegated. |
| `/market/sources` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/market_sources.py` | PARTIAL | Source/detail ownership remains delegated. |
| `/intelligence/timeline` | FastAPI/Jinja | FastAPI/Jinja | `app/web/routes_market.py` | DELEGATED | Not a Reflex-owned route. |
| `/evidence/{packet_id}` | FastAPI/Jinja | FastAPI/Jinja | `app/web/routes_market.py` | DELEGATED | Not a Reflex-owned route. |
| `/candles/{candle_id}` | FastAPI/Jinja | FastAPI/Jinja | `app/web/routes_market.py` | DELEGATED | Not a Reflex-owned route. |

## 4. Reflex route registration audit

- Required public routes are represented in the Reflex route registry and registered through `app.add_page` loops or explicit dynamic page registrations.
- Required Console routes are represented in the Reflex registry and registered in `app.py`.
- Dynamic Trace routes use Reflex bracket syntax.
- No stale `/products` or `/self-host` primary navigation route is expected to be active.
- Placeholder/baseline module semantics are documented rather than represented as full production completion.

## 5. Reflex API parity status

| Area | Status | Notes |
| --- | --- | --- |
| Public API clients | PASS | Clients use `BB_API_BASE_URL` through shared settings and consume public endpoints. |
| Trace API clients | PASS | Trace lite, report, proof-packet, and detail panel clients map to FastAPI trace endpoints and normalize safe errors. |
| Response envelope handling | PASS | The shared client unwraps envelope data and preserves safe degraded results. |
| Market API clients | PARTIAL / DELEGATED | Reflex preview clients exist, but market detail/drill-down ownership remains FastAPI/Jinja. |
| Backend domain logic | PASS | Reflex does not become the backend source of truth. |

## 6. Trace parity status

Trace is migration-primary ready but remains a deletion gate because root-suite verification is not clean.

- `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet` are registered in Reflex.
- Public address validation rejects wallet-secret-like and mnemonic-like material.
- Trace copy remains advisory-only and no-custody.
- Proof Packet copy avoids legal-proof and consensus-proof claims.
- Provider disagreement, confidence, degraded, and fallback states are represented in Trace components/tests.

## 7. Market parity/delegation status

Market ownership is **partial with explicit delegation**.

Reflex owns Market preview/navigation pages. FastAPI/Jinja remains canonical for Market detail and drill-down routes until maintainers either accept permanent delegation or migrate those details to Reflex with endpoint parity and tests.

This is acceptable for keeping Reflex primary for public/console surfaces, but it blocks deleting the legacy frontend as part of a destructive cleanup because Market ownership is not fully consolidated.

## 8. Console parity status

Console routes exist for Dashboard, Trace, Evidence, Provider Health, Market Intelligence, Time Machine, Sovereign Grid, Policy, Audit, API Explorer, and the Wow preview layer. These modules are read-only/operator-preview surfaces. The audit must not claim full production-console completion until live operator workflows and role/permission evidence are complete.

## 9. Safety/no-custody audit

| Invariant | Status | Notes |
| --- | --- | --- |
| Bitcoin-first posture | PASS | Reflex remains a frontend only. |
| No custody introduced | PASS | No wallet-secret collection path was added. |
| Public-address-only Trace input | PASS | Address validation and sensitive-input tests exist. |
| Trace advisory-only copy | PASS | Safety notices and tests cover advisory language. |
| No legal-verdict or consensus-proof claims | PASS | Trace/proof-packet copy remains limited and evidence-oriented. |
| Market not financial advice | PASS | Market copy remains intelligence/evidence oriented. |
| Degraded/fallback/stale states visible | PASS | Shared and domain-specific components exist. |

## 10. Forbidden wording audit

The repository scanner for blocked user-facing safety wording passes. Exact blocked wording is intentionally not repeated in this audit document to avoid creating new scanner findings. Remaining occurrences are limited to allowlisted tests, security helper lists, or safety scanners.

## 11. Build/test/CI status

| Command | Result | Notes |
| --- | --- | --- |
| `cd reflex_frontend && uv sync && uv run ruff check . && uv run mypy bastion_ui && uv run pytest && uv run reflex export` | PASS | Reflex-local quality, tests, and export pass with non-fatal Reflex/Node warnings. |
| `cd frontend && npm install && npm run lint && npm run typecheck && npm run test && npm run build` | PASS | Legacy rollback surface still builds; npm audit/config warnings remain. |
| `python -m pytest -q` | FAIL | Root suite has known non-Reflex/root-suite failures; deletion is blocked. |
| `make lint` | PASS | Repository lint target passes. |
| `make docs-truthfulness` | PASS | Documentation truthfulness target passes. |
| `python -m pytest -q tests/security/test_developer_layer_forbidden_wording.py` | PASS | Blocked wording scanner passes. |
| `docker compose config` | BLOCKED | Docker is unavailable in the agent environment. |
| `make reflex-docker-build` | BLOCKED | Docker is unavailable in the agent environment. |
| `make runtime-render-compose` | PASS | Runtime compose render passes. |
| `make runtime-render-k3s` | PASS | Runtime k3s render passes. |
| `make runtime-render-k8s` | PASS | Runtime k8s render passes. |

## 12. Deployment references audit

Active runtime and docs references to Next.js remain intentionally present for rollback and parallel validation. Because the destructive cleanup requested removing the old runnable frontend, these active references are a blocker rather than something to delete blindly.

Required Reflex deployment references exist: `reflex_frontend/`, `BB_API_BASE_URL`, Reflex Dockerfile, Reflex compose services, and runtime-profile metadata. Docker verification must still run on a Docker-capable host before deleting the rollback frontend.

## 13. Documentation truthfulness audit

Docs now distinguish Reflex primary/preferred status from completed physical removal. The final archive record is pending rather than completed. Production readiness is not claimed, and Market detail delegation remains explicit.

## 14. Deletion readiness decision

Decision: **DELETION BLOCKED**.

`frontend/` was **not** deleted.

Blocking reasons:

1. Root `python -m pytest -q` fails.
2. Docker build/config checks cannot run in this environment.
3. Market detail/drill-down ownership remains delegated.
4. Active rollback references to Next.js remain in deployment/docs/CI material.
5. Formal accessibility/manual browser audit evidence is still incomplete.

## 15. Rollback note

Rollback remains available by keeping `frontend/` intact and using the documented legacy/parallel runtime modes. Operators can still run Reflex-only, Next.js-only, or parallel frontend modes from the existing compose/runtime profile documentation.

## 16. Final recommendation

Do not remove Next.js in this PR. Create a follow-up cleanup only after the root suite is fixed or scoped, Docker checks pass on CI, Market delegation is accepted as permanent or migrated, and maintainers explicitly approve removing the rollback frontend.

## 17. Final readiness scores

| Area | Score | Rationale |
| --- | ---: | --- |
| Reflex Route Readiness | 92% | Public/Trace/Console routes are registered; Market details are delegated. |
| Reflex API Parity Readiness | 88% | Public/Trace pass; Market detail parity remains delegated. |
| Trace Migration Readiness | 92% | Trace route/API/safety coverage is strong; root suite still blocks deletion. |
| Market Ownership Readiness | 70% | Preview routes exist; detail routes remain FastAPI/Jinja-owned. |
| Console Readiness | 76% | Baseline modules exist; not all are production-grade operator workflows. |
| Safety/No-Custody Readiness | 96% | Tests and copy enforce no-custody posture. |
| Accessibility Readiness | 70% | Baseline helpers/tests exist; formal manual audit remains. |
| Build/CI Readiness | 72% | Reflex and lint/docs checks pass; root and Docker gates block. |
| Deployment Readiness | 70% | Reflex runtime metadata exists; active rollback refs remain. |
| Legacy Removal Readiness | 35% | Legacy deletion is blocked. |
| Overall Frontend Cutover Readiness | 76% | Reflex is strong as preferred frontend, but destructive cleanup is not ready. |
