# Final Reflex Migration Audit — Prompt 22/22

## Executive summary

Final decision: **Reflex remains the preferred primary migration frontend, but the legacy Next.js frontend must stay in `frontend/` as a rollback surface.**

Next.js archive decision: **B. Mark Next.js as legacy but keep in `frontend/`.**

Reflex public, Trace, Console, API-client, safety, no-custody, route parity, and export checks are strong enough to keep Reflex as the preferred primary runtime mode introduced in Prompt 21/22. The migration is not eligible for physical Next.js archive or deletion because Market detail ownership remains intentionally delegated to FastAPI/Jinja, root repository tests still have known non-Reflex failures, local Docker is unavailable in this agent environment, and formal accessibility/responsive audit evidence is not complete.

No backend domain logic moved into Reflex. No custody, signing, wallet-secret, seed, wallet-file, keystore, mining, Stratum, or distributed backend mesh behavior was introduced.

## Final frontend ownership table

| Route | Expected owner | Actual owner | Implementation path | Backend dependency | Status | Blocker | Rollback path |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/home.py` | public landing/status data | PASS | none | Next.js `/` in `frontend/app/page.tsx` |
| `/platform` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/platform.py` | static/public copy | PASS | none | Next.js `/platform` |
| `/developers` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/developers.py` | static/docs links | PASS | deeper docs remain static | Next.js `/developers` |
| `/operations` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/operations.py` | static/operator guidance | PASS | none | Next.js `/operations` |
| `/manifesto` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/manifesto.py` | static | PASS | none | Next.js `/manifesto` |
| `/evidence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/evidence.py` | evidence/public adapters | PASS | backend data may degrade | Next.js `/evidence` |
| `/status` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/status.py` | `/api/v1/public/status` | PASS | none | Next.js `/status` |
| `/roadmap` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/roadmap.py` | `/api/v1/public/roadmap` | PASS | none | Next.js `/roadmap` |
| `/security` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/security.py` | static/security | PASS | none | Next.js `/security` |
| `/docs` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/docs.py` | docs/static links | PASS | deeper docs are links | Next.js `/docs` |
| `/check` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/check.py` | `/api/v1/trace/lite/{address}` | PASS | none | Next.js `/check` |
| `/trace` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/trace.py` | Trace client | PASS | none | Next.js `/trace` |
| `/trace/[report_id]` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/trace_report.py` | public summary, Trace report APIs | PASS | none | Next.js `/trace/[reportId]` |
| `/trace/[report_id]/proof-packet` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/proof_packet.py` | Trace proof packet API | PASS | none | Next.js proof packet route |
| `/console` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console.py` | console adapters | PASS | preview/operator baseline | Run Next.js rollback plus API/Jinja surfaces |
| `/console/trace` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_trace.py` | Trace status/events | PASS | preview/operator baseline | API/Jinja + legacy diagnostic routes |
| `/console/evidence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_evidence.py` | evidence adapters | PASS | preview/operator baseline | API/Jinja evidence views |
| `/console/market-intelligence` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_market_intelligence.py` | Market adapters | PASS | read-only preview | FastAPI/Jinja Market dashboard |
| `/console/time-machine` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_time_machine.py` | Time Machine adapters | PASS | read-only preview | FastAPI/Jinja Market dashboard |
| `/console/sovereign-grid` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_sovereign_grid.py` | readiness adapters | PASS | readiness view only | Disable Reflex console; keep API backend |
| `/console/policy` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_policy.py` | policy review APIs | PASS | review/draft only | Disable Reflex console; use backend policy checks |
| `/console/audit` | Reflex | Reflex | `reflex_frontend/bastion_ui/routes/console_audit.py` | audit adapters | PASS | read-only preview | backend/admin audit surfaces |
| `/market` | Reflex primary preview or delegated | Reflex preview + FastAPI/Jinja active | `reflex_frontend/bastion_ui/routes/market.py`, `app/web/routes_market.py` | market/time-machine DTOs | PARTIAL / DELEGATED | FastAPI/Jinja remains canonical for detail/fallback | FastAPI/Jinja `/market` |
| `/market/timeline` | Reflex preview or delegated | Reflex preview + FastAPI/Jinja active | `reflex_frontend/bastion_ui/routes/market_timeline.py`, `app/web/routes_market.py` | timeline DTOs | PARTIAL / DELEGATED | detail ownership remains Jinja | FastAPI/Jinja `/market/{section}` |
| `/market/time-machine` | Reflex preview or delegated | Reflex preview + FastAPI/Jinja active | `reflex_frontend/bastion_ui/routes/market_time_machine.py`, `app/web/routes_market.py` | `/web/market-time-machine` | PARTIAL / DELEGATED | full parity not claimed | FastAPI/Jinja `/market/time-machine` |
| `/market/signals` | Reflex preview | Reflex preview | `reflex_frontend/bastion_ui/routes/market_signals.py` | signal adapters | PARTIAL | read-only preview | FastAPI/Jinja Market dashboard |
| `/market/evidence` | Reflex preview | Reflex preview | `reflex_frontend/bastion_ui/routes/market_evidence.py` | evidence adapters | PARTIAL | detail route delegated | FastAPI/Jinja evidence route |
| `/market/narratives` | Reflex preview | Reflex preview | `reflex_frontend/bastion_ui/routes/market_narratives.py` | narrative adapters | PARTIAL | read-only preview | FastAPI/Jinja Market dashboard |
| `/market/sources` | Reflex preview | Reflex preview | `reflex_frontend/bastion_ui/routes/market_sources.py` | source adapters | PARTIAL | read-only preview | FastAPI/Jinja Market dashboard |
| `/intelligence/timeline` | FastAPI/Jinja delegated | FastAPI/Jinja | `app/web/routes_market.py` | timeline service | DELEGATED | intentionally backend-rendered | keep FastAPI/Jinja |
| `/evidence/{packet_id}` | FastAPI/Jinja delegated | FastAPI/Jinja | `app/web/routes_market.py` | evidence panel/replay | DELEGATED | intentionally backend-rendered | keep FastAPI/Jinja |
| `/candles/{candle_id}` | FastAPI/Jinja delegated | FastAPI/Jinja | `app/web/routes_market.py` | candle attribution | DELEGATED | intentionally backend-rendered | keep FastAPI/Jinja |

## Reflex route audit

- Required public routes are represented in the Reflex route registry and app registration.
- Required Console routes are represented in the Reflex route registry and tests.
- Dynamic Trace routes use the migration target `[report_id]` naming.
- Market preview routes exist in Reflex, but FastAPI/Jinja remains delegated for detail and fallback routes.
- Placeholder/baseline modules are not treated as production-complete control planes.

## API parity audit

Public API checks:

| Endpoint | Status | Notes |
| --- | --- | --- |
| `/api/v1/public/landing` | PASS | backend exists; public client can consume envelope data |
| `/api/v1/public/status` | PASS | backend exists and Reflex fallback/degraded handling exists |
| `/api/v1/public/roadmap` | PASS | backend exists |
| `/api/v1/public/stats` | PASS | backend exists |
| `/api/v1/public/features` | PASS | backend exists |
| `/api/v1/public/trace/{report_id}/summary` | PASS | backend exists; Trace report summary path documented |

Trace API checks:

| Endpoint | Status | Notes |
| --- | --- | --- |
| `/api/v1/trace/lite/{address}` | PASS | used by `/check` and Trace Lite |
| `/api/v1/trace/address/{address}` | PASS | full address analysis endpoint exists |
| `/api/v1/trace/report/{report_id}` | PASS | report endpoint exists |
| `/api/v1/trace/report/{report_id}/evidence` | PASS | evidence endpoint exists |
| `/api/v1/trace/report/{report_id}/privacy-shield` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/origin-passport` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/source-summary` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/provider-disagreement` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/utxo-hygiene` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/dust-radar` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/counterparty-lens` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/policy-facts` | PASS | panel endpoint exists |
| `/api/v1/trace/report/{report_id}/proof-packet` | PASS | proof packet endpoint exists |
| `/api/v1/trace/status` | PASS | console status endpoint exists |
| `/api/v1/trace/events` | PASS | console/audit endpoint exists |

Market/API DTO checks:

| Endpoint | Status | Notes |
| --- | --- | --- |
| `/web/market-time-machine` | DELEGATED | FastAPI/Jinja DTO remains canonical |
| `/web/timeline` | DELEGATED | FastAPI/Jinja DTO remains canonical |
| `/web/candle/{candle_id}` | DELEGATED | DTO route supports candle detail |
| `/web/evidence/{packet_id}` | DELEGATED | DTO route supports evidence detail |

Mismatches left open:

- Market detail and drill-down routes are intentionally delegated instead of fully migrated.
- Provider/audit/admin endpoint shapes may evolve and should remain degraded-safe in Reflex.
- No API mismatch justifies deleting Next.js in this prompt.

## ResponseEnvelope audit

| Behavior | Status | Notes |
| --- | --- | --- |
| `ResponseEnvelope.data` unwrap | PASS | covered by Reflex API client tests |
| 400 handling | PASS | safe public error normalization |
| 401 handling | PASS | normalized safe error class path |
| 403 handling | PASS | normalized safe error class path |
| 404 handling | PASS | report-not-found/user-safe copy |
| 422 handling | PASS | validation-safe handling |
| 429 handling | PASS | rate-limit-safe handling |
| 500 handling | PASS | generic backend-unavailable style copy |
| timeout handling | PASS | timeout normalization |
| stale/degraded state handling | PASS | reusable degraded/stale/fallback components and tests |
| safe generic fallback error message | PASS | public messages avoid stack/secret leakage |

## Trace final audit

Trace status: **PASS for migration-primary; not a legal or consensus-proof system**.

- `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet` are implemented in Reflex.
- Address validation is public-address-only and rejects sensitive material before API calls.
- Trace safety copy preserves advisory-only, no-custody, not legal verification, not Bitcoin consensus proof, and public-address-only language.
- Trace report and Proof Packet pages remain evidence-context surfaces and do not claim legal proof or consensus proof.
- Confidence, degraded, limitations, provider disagreement, and low-confidence concepts are represented in components/tests.

Trace blockers:

- Root suite still contains an older route-contract assertion that should be reconciled with the Reflex route registry/app-registration pattern.
- Formal live-backend browser smoke evidence is still needed before a production readiness claim.

## Market final audit

Market status: **PARTIAL / DELEGATED**.

- Reflex has preview routes for the requested Market route family.
- FastAPI/Jinja remains intentionally canonical for Market detail/fallback and DTO routes.
- Market copy remains historical/advisory context only, not financial advice, not prediction, and not a trading signal.

Market blockers:

- Do not mark Market migration complete while `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}` remain FastAPI/Jinja-delegated.
- Evidence drill-down and candle drill-down remain backend-rendered/delegated.
- Full production visual parity and live DTO parity evidence remain Prompt 22 follow-up items for a separate cleanup/archive decision.

## Console final audit

Console status: **BASELINE / PREVIEW PASS**.

| Module | Status | Notes |
| --- | --- | --- |
| Dashboard | baseline | overview shell exists |
| Trace | baseline | read-only/operator visibility |
| Evidence | baseline | degraded-safe evidence summaries |
| Provider Health | baseline | provider health visibility, endpoint shape may evolve |
| Market Intelligence | baseline | read-only preview |
| Time Machine | baseline | read-only preview |
| Sovereign Grid | baseline | readiness view only, no mesh/mining claims |
| Policy Engine | baseline | draft/review only, no execution |
| Audit Log | baseline | read-only audit visibility |
| Deployment Status | placeholder | not production control-plane |
| API Explorer | baseline | inspection/read-only focused |

## Navigation final audit

- Required public navigation labels are present: Platform, Trace, Evidence, Status, Developers, Operations, Docs, Security, and Roadmap.
- Stale `/products` and `/self-host` are not primary Reflex navigation entries.
- Command palette includes required Trace, Check, Evidence, Status, Console, Market Intelligence, Time Machine, Sovereign Grid, Policy, and Audit actions.

## Forbidden wording audit

Repository-wide scanner tests pass for the developer-layer blocked phrase set. New final audit docs intentionally avoid spelling out the blocked phrase set to keep the repository-wide scanner green outside its dedicated allowlist.

## No-custody input audit

| Route | Component | Expected input | Validation | Sensitive input risk | Status |
| --- | --- | --- | --- | --- | --- |
| `/check` | Trace address form/input | public Bitcoin address | public-address and sensitive-material detector | user paste of wallet-secret material | PASS |
| `/trace` | Trace public flow | public Bitcoin address/report flow | same detector before API call | user paste of wallet-secret material | PASS |
| `/trace/[report_id]` | report id route | report id | report id validation | low | PASS |
| `/trace/[report_id]/proof-packet` | report id route | report id | report id validation | low | PASS |
| Console API Explorer | safe example input only | endpoint/template examples | unsafe actions labelled inspection-only/admin/review | medium | BASELINE |
| Policy Console | draft/review fields | policy facts/review | no execution/custody action | medium | BASELINE |

No input should request custody material, signing material, wallet files, keystores, private keys, mnemonic-like phrases, or extended private keys.

## Accessibility and responsive audit

Status: **BASELINE / PARTIAL**.

- Keyboard/focus helpers, labels, reduced-motion helpers, responsive layout helpers, and accessibility docs exist.
- Loading, empty, error, degraded, stale, and fallback states are represented in shared components and tests.
- Formal WCAG conformance, screen-reader pass, contrast pass, and mobile/tablet/desktop manual screenshots remain required before production-readiness claims.

## CI/build/test audit

Status: **PARTIAL PASS**.

- Reflex CI covers lint, mypy, tests, export, Docker build wiring, route parity, and safety checks.
- Local Reflex sync/lint/typecheck/tests/export passed.
- Legacy Next.js install/lint/typecheck/tests/build passed and remains rollback-capable.
- Root `python -m pytest -q` still fails on known non-Reflex/root-suite blockers.
- Docker build could not be run locally because Docker is unavailable in this agent environment.
- Reflex workflow does not replace a broader backend/Next.js production pipeline; keep existing checks.

## Docker/runtime integration audit

- Reflex Dockerfile exists.
- Reflex compose services exist for standalone, full-Reflex, and parallel-frontends modes.
- Ports are separated: Next.js `3000`, Reflex frontend `3001`, Reflex backend/control `8001`, FastAPI `8000`.
- `BB_API_BASE_URL` is documented in Reflex env/compose docs.
- Runtime profile metadata marks Reflex as preferred primary for migration while keeping rollback.
- Production profile does not require a cloud provider.

## Documentation truthfulness audit

- Docs now distinguish preferred primary, delegated, baseline, preview, partial, rollback, blocker, and archive states.
- No document should claim full Market migration while FastAPI/Jinja owns detail routes.
- No document should claim production readiness without Docker/live/a11y/root-suite evidence.
- Next.js is legacy/rollback, not physically archived or deleted.

## Final readiness scores

| Area | Score | Reason |
| --- | ---: | --- |
| Reflex Route Readiness | 92% | required public/Trace/Console routes exist; Market detail delegated |
| Reflex API Parity Readiness | 88% | required public/Trace endpoints align; Market/admin/provider shapes remain partial |
| Trace Migration Readiness | 92% | Trace route/API/safety tests pass; live browser evidence still needed |
| Market Migration Readiness | 62% | preview routes exist but canonical detail routes remain FastAPI/Jinja-delegated |
| Console Readiness | 76% | baseline modules exist; some modules are preview/placeholders |
| Safety/No-Custody Readiness | 96% | safety copy and sensitive-input tests pass |
| Accessibility Readiness | 70% | baseline exists; formal audit not complete |
| Build/CI Readiness | 82% | Reflex/legacy builds pass; root and Docker local blockers remain |
| Legacy Archive Readiness | 55% | rollback works but archive criteria are not all satisfied |
| Overall Frontend Migration Readiness | 82% | Reflex can remain preferred primary, but full archive is blocked |


## Verification command results

| Command | Result | Notes |
| --- | --- | --- |
| `cd reflex_frontend && uv sync && uv run ruff check . && uv run mypy bastion_ui && uv run pytest && uv run reflex export` | PASS | Reflex-local sync/lint/typecheck/tests/export passed; export emitted non-fatal Reflex/Node warnings. |
| `cd frontend && npm install && npm run lint && npm run typecheck && npm run test && npm run build` | PASS | Legacy Next.js rollback surface passed; npm reported existing audit/config warnings. |
| `python -m pytest -q tests/security/test_developer_layer_forbidden_wording.py` | PASS | Developer-layer blocked wording scanner passed. |
| `make lint` | PASS | Ruff and mypy passed for root app/cli/tests scope. |
| `make docs-truthfulness` | PASS | Docs truthfulness scanner passed. |
| `make runtime-render-compose` | PASS | Runtime profile dry-run rendered compose plan. |
| `make runtime-render-k3s` | PASS | Runtime profile dry-run rendered K3s plan. |
| `make runtime-render-k8s` | PASS | Runtime profile dry-run rendered Kubernetes plan. |
| `python -m pytest -q` | FAIL | 14 known non-Reflex/root-suite failures remain. |
| `docker compose config` | BLOCKED | Docker unavailable in this agent environment. |
| `make reflex-docker-build` | BLOCKED | Docker unavailable in this agent environment. |

## Final decision

- Reflex primary status: **preferred primary migration frontend**.
- Next.js archive status: **legacy rollback, keep in `frontend/`**.
- Market status: **partial/delegated**.
- Production readiness: **not claimed**.
