# Implementation Baseline Audit

Repository: `Hegehub/bitcoinbastion`  
Audit date: 2026-06-06  
Scope: contract-freeze audit only. No product feature implementation, runtime feature addition, migrations, or application refactor was performed.

## 1. Repository Structure Audit

| Path | Present | Purpose | Current maturity | Status | Future prompt guidance |
| --- | --- | --- | --- | --- | --- |
| `app/` | yes | FastAPI backend, API routers, services, DB models/repositories, web dashboard, background/task helpers. | Active backend baseline with many implemented domains and placeholder/baseline subsystems. | Active. | Modify for backend contract alignment only after API contract prompts; do not add event/webhook/WebSocket features before event taxonomy/outbox prompts. |
| `frontend/` | yes | Existing Next.js public/frontend layer with routes, components, services, tests, Tailwind/Next config. | Active public UI baseline; Trace UI exists but navigation/API contract gaps remain. | Active. | Preserve as canonical public frontend until an explicit future switch plan; Reflex must be parallel only. |
| `app/web/` | yes | FastAPI/Jinja server-rendered Market Intelligence / Market Time Machine dashboard plus static assets. | Active server-rendered dashboard with DTO-style `/web/*` routes. | Active. | Do not remove; do not let Reflex or Next.js silently take over `/market` without route ownership plan. |
| `deploy/` | yes | Deployment documentation/manifests, primarily Kubernetes. | Active deployment foundation. | Active. | Extend runtime profiles here as canonical deployment path. |
| `deploy/kubernetes/` | yes | Canonical Kubernetes manifests, overlays, runbooks, operations/evidence/security/gitops artifacts. | Mature baseline/RC-ready pending environment evidence; dev/staging/production overlays exist. | Canonical active path. | Future runtime prompts should modify this path first. |
| `k8s/` | yes | Older/parallel Kubernetes manifests with frontend service/deployment and basic overlays. | Legacy/parallel; tests still reference it. | Legacy/unclear. | Do not delete yet; reconcile tests/path ownership in a dedicated runtime prompt. |
| `docs/` | yes | Architecture, API, readiness, Trace, Kubernetes, frontend, operations, truthfulness docs. | Active, but contains stale claims and historical status contradictions. | Active with drift. | Update incrementally after contract fixes; do not make production-ready claims without evidence. |
| `tests/` | yes | Python unit/integration/contract/deployment/security/regression tests. | Active, but at least deployment tests reference legacy `k8s/`. | Active with known path drift. | Keep tests; update legacy assumptions only in focused prompts. |
| `scripts/` | yes | Utility checks, docs truthfulness, security/deployment validation, smoke helpers. | Active support tooling. | Active. | Use for verification and docs checks. |
| `sdk/` | no | No repository-root SDK package found. | Not implemented. | Missing. | Add only after public API contract stabilization. |
| `cli/` | no root `cli/`; `app/cli/` exists | Backend seed scripts for news/narratives. | Minimal internal CLI scripts, not public developer CLI. | Partial/internal. | Public CLI should be a future package with stable API contracts; do not repurpose seed scripts. |
| `mcp/` | no | No MCP connector package found. | Not implemented. | Missing. | Add after SDK/API/event contracts stabilize. |

## 2. Backend API Router Audit

`app/main.py` creates a FastAPI app, applies middleware/exception/OpenAPI setup, includes API routers under `settings.api_prefix` (currently expected `/api/v1`), includes root health routes without the API prefix, mounts `/static`, and includes the FastAPI/Jinja market web router without an API prefix.

| router_name | Source module | Effective prefix | Domain | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `health_root_router` | `app.api.health_root` | `/health` | root health/ops | Active public/internal health | Duplicates some provider/live/ready semantics outside `/api/v1`. |
| `health_router` | `app.api.v1.health` | `/api/v1/health` | health | Active | Frontend/status/deployment-facing readiness and degraded state candidate. |
| `auth_router` | `app.api.v1.auth` | `/api/v1/auth` | auth | Active | Public auth endpoints; not currently used by public frontend audit surface. |
| `news_router` | `app.api.v1.news` | `/api/v1/news` | news | Active | Event-publishing candidate. |
| `market_intelligence_router` | `app.api.v1.market_intelligence` | `/api/v1/news` | market intelligence | Active | Market/event-publishing candidate. |
| `market_data_router` | `app.api.v1.market_data` | `/api/v1/market` | market data | Active | Provider/stale/degraded event candidate. |
| `market_router` | `app.api.v1.market` | `/api/v1/market` | market | Active | Frontend/server dashboard candidate; event-publishing candidate. |
| `metrics_status_router` | `app.api.v1.metrics_status` | `/api/v1/metrics` | metrics/status | Active | Observability candidate. |
| `intelligence_timeline_router` | `app.api.v1.intelligence_timeline` | `/api/v1/intelligence/timeline` | intelligence timeline | Active | Frontend/Jinja dashboard supporting API. |
| `intelligence_router` | `app.api.v1.intelligence` | `/api/v1/intelligence` | intelligence | Active | Large market memory/narrative/candle domain; event-publishing candidate. |
| `signals_router` | `app.api.v1.signals` | `/api/v1/signals` | signals | Active | Shares `/signals` prefix with intelligence-signals router. |
| `intelligence_signals_router` | `app.api.v1.intelligence_signals` | `/api/v1/signals` | intelligence signals | Active | Duplicate prefix with `signals_router`; routes appear non-conflicting today but must be frozen carefully. |
| `operator_signals_router` | `app.api.v1.operator_signals` | `/api/v1/operator/signals` | operator signals | Active | Internal/operator-facing signal governance. |
| `onchain_router` | `app.api.v1.onchain` | `/api/v1/onchain` | onchain | Active | Event-publishing candidate. |
| `entities_router` | `app.api.v1.entities` | `/api/v1/entities` | entities | Active | Watchlist/provenance event candidate. |
| `wallet_router` | `app.api.v1.wallet` | `/api/v1/wallet` | wallet health profiles | Active no-custody health | Event candidate only for wallet-health metadata, never custody/signing material. |
| `fees_router` | `app.api.v1.fees` | `/api/v1/fees` | fees | Active | Advisory fee recommendation. |
| `treasury_router` | `app.api.v1.treasury` | `/api/v1/treasury` | treasury approvals | Active | Event-publishing candidate; must preserve operator approval/no-custody posture. |
| `admin_router` | `app.api.v1.admin` | `/api/v1/admin` | admin | Active internal/admin | Includes jobs/audit logs; internal/admin. |
| `users_router` | `app.api.v1.users` | `/api/v1/users` | users | Active internal/auth | Internal/admin-facing. |
| `policy_router` | `app.api.v1.policy` | `/api/v1/policy` | policy | Active | Event candidate for policy decisions. |
| `privacy_router` | `app.api.v1.privacy` | `/api/v1/privacy` | privacy | Active | Trace/privacy-adjacent. |
| `education_router` | `app.api.v1.education` | `/api/v1/education` | education | Active | Public-ish informational route. |
| `evidence_router` | `app.api.v1.evidence` | `/api/v1/evidence` | evidence/replay | Active | Frontend-facing and event-publishing candidate. |
| `observability_router` | `app.api.v1.observability` | `/api/v1/observability` | observability | Active | Runtime/provider-health event candidate. |
| `operations_router` | `app.api.v1.operations` | `/api/v1/operations` | operations | Active | Operator/deployment readiness candidate. |
| `citadel_router` | `app.api.v1.citadel` | `/api/v1/citadel` | citadel | Active | Future event candidate. |
| `trace_router` | `app.api.v1.trace` | `/api/v1/trace` | Trace | Active baseline, migration blocker | Frontend-facing; several advisory/business/enterprise endpoints; missing report-scoped proof-packet GET. |
| `public_router` | `app.api.v1.public` | `/api/v1/public` | public site/public Trace | Active public | Used by Next.js public pages and Trace summary. |
| `market_time_machine_web_router` | `app.web.routes_market` | no API prefix | FastAPI/Jinja web market routes | Active server-rendered | Owns `/market` at FastAPI runtime if mounted directly. |

### Duplicate/conflicting prefixes

- `/api/v1/signals` is used by both `app.api.v1.signals` and `app.api.v1.intelligence_signals`. Current route suffixes do not visibly collide, but future additions must check both modules before adding any `/signals/*` route.
- `/api/v1/news` is used by both `app.api.v1.news` and `app.api.v1.market_intelligence`; future `/news/*` additions must check both modules.
- `/api/v1/market` is used by both `app.api.v1.market` and `app.api.v1.market_data`; future `/market/*` additions must check both modules and the FastAPI/Jinja `/market` page route.
- `/health/*` root routes and `/api/v1/health/*` API routes overlap in semantics (`live`, `ready`, `providers`) but are intentionally separate public/root vs versioned API surfaces.
- `/market` exists both as a Next.js route (`frontend/app` does not currently include `/market`) expectation in the prompt and as FastAPI/Jinja route. Current repository has no Next.js `frontend/app/market` pages; FastAPI/Jinja owns the implemented `/market` server route.

### Public vs admin/internal routes

- Public/frontend-facing: `/api/v1/public/*`, `/api/v1/trace/lite/*`, `/api/v1/trace/report/*`, `/api/v1/evidence/*`, `/api/v1/market*`, `/api/v1/intelligence*`, `/api/v1/health*`.
- Admin/internal/operator: `/api/v1/admin/*`, `/api/v1/users/*`, many `/api/v1/operations/*`, `/api/v1/operator*`, treasury approvals, and signal governance review endpoints.

### Event publishing candidates

Future event taxonomy should include signals, intelligence/news, market data/provider health, onchain observations, Trace report lifecycle, evidence packet lifecycle, treasury request decisions, policy decisions, wallet-health metadata, observability/degraded states, and operations/runtime readiness changes.

## 3. Trace Contract Audit

Audited files/areas: `app/api/v1/trace.py`, `app/api/v1/public.py`, `app/db/models/bastion_trace.py`, `app/db/repositories/bastion_trace_repository.py`, `app/services/bastion_trace/`, `docs/BASTION_TRACE*.md`, `docs/TRACE*.md`, `frontend/app/check/`, `frontend/app/trace/`, `frontend/components/trace/`, and `frontend/tests/trace-report-ui.test.tsx`.

Trace backend is an active advisory baseline with DB-backed reports/evidence, source status, watchlist, privacy/origin/counterparty/policy facets, business/enterprise placeholders, runtime status/events/alerts, and public Trace summary. It is not production-calibrated.

| Method | Path | Handler | Response envelope type | Used by frontend | Implemented | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/trace/address/{address}` | `analyze_address` | `ResponseEnvelope[TraceReport]` | unknown/no current Next.js call | yes | Rejects sensitive wallet material; creates/returns report. |
| GET | `/api/v1/trace/report/{report_id}` | `get_report` | `ResponseEnvelope[TraceReport]` | API client method exists; current report page uses public summary instead | yes | Full Trace report backend contract. |
| GET | `/api/v1/trace/report/{report_id}/evidence` | `list_evidence` | `ResponseEnvelope[list[TraceEvidence]]` | unknown/no current direct Next.js call | yes | Evidence list. |
| GET | `/api/v1/trace/lite/{address}` | `lite_address_check` | `ResponseEnvelope[dict[str, object]]` | yes (`AddressCheckForm`) | yes | Frontend expects at least `report_id`; backend returns dict envelope. |
| GET | `/api/v1/public/trace/{report_id}/summary` | `public_trace_summary` | `ResponseEnvelope[PublicTraceSummary]` | yes (`AddressCheckForm`, `/trace/[reportId]`) | yes | Public-safe summary. |
| GET | `/api/v1/trace/report/{report_id}/privacy-shield` | `get_privacy_shield` | `ResponseEnvelope[dict[str, object]]` | unknown/no current direct call | yes | Privacy facet. |
| GET | `/api/v1/trace/report/{report_id}/origin-passport` | `get_origin_passport` | `ResponseEnvelope[dict[str, object]]` | unknown/no current direct call | yes | Origin facet. |
| GET | `/api/v1/trace/report/{report_id}/counterparty-lens` | `get_counterparty_lens` | `ResponseEnvelope[dict[str, object]]` | unknown/no current direct call | yes | Counterparty facet. |
| GET | `/api/v1/trace/report/{report_id}/policy-facts` | `trace_policy_facts` | `ResponseEnvelope[dict[str, object]]` | unknown/no current direct call | yes | Policy bridge facts. |
| GET | `/api/v1/trace/report/{report_id}/proof-packet` | none | expected by frontend `getProofPacket` and `/trace/[reportId]/proof-packet` route | yes | no | Important mismatch. Backend has `POST /api/v1/trace/enterprise/proof-packet`, but no report-scoped public/frontend GET. |
| GET | `/api/v1/trace/status` | `trace_status` | `ResponseEnvelope[dict[str, object]]` | API client method exists | yes | Operational Trace status. |
| GET | `/api/v1/trace/events` | `trace_events` | `ResponseEnvelope[list[dict[str, object]]]` | API client method exists | yes | Runtime events baseline, not WebSocket. |

Additional implemented Trace endpoints include: `/sources`, `/sources/{source_name}`, `/watchlist` GET/POST, `/source-summary`, `/provider-disagreement`, `/utxo-hygiene`, `/dust-radar`, `/payment-context`, `/payment-intent/preview`, `/destination-review`, business profile/batch/policy-profiles/events, enterprise profile/RBAC/SSO/evidence access, enterprise proof-packet POST, citadel contribution, treasury destination check, register advisory, evidence refs, `/events/{event_id}`, and `/alerts`.

### Trace migration blocker findings

1. Trace exists across backend and frontend and must be treated as a frozen baseline before Reflex migration.
2. The public summary route is implemented and used by the Next.js Trace report page.
3. The proof-packet frontend route exists, but the expected GET backend endpoint is missing.
4. Trace status/events are implemented as REST endpoints; no WebSocket stream exists and should not be added before event taxonomy/outbox planning.
5. Trace docs contain baseline/not-production-calibrated language, but other docs still say Website UI is pending; that is stale because Next.js Trace pages/components now exist.

## 4. Frontend Route Audit

Current Next.js routes discovered under `frontend/app/`:

| Route | File path | Implemented | Uses backend API | Backend endpoints used | Known mismatch | Tests |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | `frontend/app/page.tsx` | yes | indirect/components only | public hooks/components may show status/stats | none in this audit | homepage/foundation/pages tests. |
| `/platform` | `frontend/app/platform/page.tsx` | yes | no direct call seen | none | Header label still says Products via translation key while href is `/platform`. | navigation/pages tests partial. |
| `/developers` | `frontend/app/developers/page.tsx` | yes | documents APIs, no runtime call | `/api/v1/public/*` listed | none; docs only. | pages tests. |
| `/developers/api` | `frontend/app/developers/api/page.tsx` | yes | examples only | public API examples | none. | not specific. |
| `/developers/webhooks` | `frontend/app/developers/webhooks/page.tsx` | yes | no | none | Correctly states webhook contracts are not published. | not specific. |
| `/developers/changelog` | `frontend/app/developers/changelog/page.tsx` | yes | no | none | none. | not specific. |
| `/developers/contributing` | `frontend/app/developers/contributing/page.tsx` | yes | no | none | none. | not specific. |
| `/developers/examples` | `frontend/app/developers/examples/page.tsx` | yes | examples only | public API examples | none. | not specific. |
| `/operations` | `frontend/app/operations/page.tsx` | yes | no direct call seen | none | Former self-host CTA points here; command palette still links `/self-host`. | navigation partial. |
| `/manifesto` | `frontend/app/manifesto/page.tsx` | yes | no | none | none. | pages. |
| `/evidence` | `frontend/app/evidence/page.tsx` | yes | no direct call seen | none | API-backed evidence dashboard not confirmed from route. | pages maybe. |
| `/status` | `frontend/app/status/page.tsx` | yes | likely public hooks | `/api/v1/public/status`, public stats via frontend lib/hook | none found in apiClient for stats but public docs list it. | status-page test. |
| `/roadmap` | `frontend/app/roadmap/page.tsx` | yes | no direct call seen | none | none. | pages. |
| `/security` | `frontend/app/security/page.tsx` | yes | no | none | none. | hardening/security coverage. |
| `/docs` | `frontend/app/docs/page.tsx` | yes | no | none | none. | pages. |
| `/check` | `frontend/app/check/page.tsx` | yes | yes through `AddressCheckForm` | `/api/v1/trace/lite/{address}`, `/api/v1/public/trace/{report_id}/summary` | Works if lite returns `report_id`; shape typed narrowly. | lite-check test. |
| `/trace` | `frontend/app/trace/page.tsx` | yes | likely form/components | `/api/v1/trace/lite/{address}` and public summary via form if present | Not exposed in SiteHeader. | trace/lite tests. |
| `/trace/[reportId]` | `frontend/app/trace/[reportId]/page.tsx` | yes | yes | `/api/v1/public/trace/{report_id}/summary` | Uses public summary only, not full report. | trace-report-ui test. |
| `/trace/[reportId]/proof-packet` | `frontend/app/trace/[reportId]/proof-packet/page.tsx` | yes | unclear/direct page content not audited deeply | frontend service expects `/api/v1/trace/report/{report_id}/proof-packet` | Backend GET missing. | trace-report-ui likely references proof-packet link. |
| `/market` | no Next.js file | no | n/a | n/a | Implemented by FastAPI/Jinja, not Next.js. | n/a. |
| `/market/timeline` | no Next.js file | no | n/a | n/a | Server has `/intelligence/timeline`, not Next route. | n/a. |
| `/market/time-machine` | no Next.js file | no | n/a | n/a | FastAPI/Jinja implements `/market/time-machine`. | n/a. |
| `/market/signals` | no Next.js file | no | n/a | n/a | FastAPI/Jinja dynamic `/market/{section}` likely handles. | n/a. |
| `/market/evidence` | no Next.js file | no | n/a | n/a | FastAPI/Jinja dynamic `/market/{section}` likely handles. | n/a. |
| `/market/narratives` | no Next.js file | no | n/a | n/a | FastAPI/Jinja dynamic `/market/{section}` likely handles. | n/a. |
| `/market/sources` | no Next.js file | no | n/a | n/a | FastAPI/Jinja dynamic `/market/{section}` likely handles. | n/a. |
| `/products` and subroutes | multiple `frontend/app/products/*` | yes | no direct calls seen | none | Legacy/outdated relative to current `/platform` nav direction but still implemented. | pages may cover. |
| `/self-host` and subroutes | multiple `frontend/app/self-host/*` | yes | no direct calls seen | none | Legacy/outdated relative to `/operations` CTA but still implemented. | selfhost tests. |
| `/dashboard/*` | multiple `frontend/app/dashboard/*` | yes | some UI likely static/mock | runtime events/status pages | Internal dashboard baseline; not in public nav audit list. | platform-dashboard-ui. |
| `/citadel`, `/treasury`, `/enterprise`, `/register`, `/genesis`, `/blog`, `/design-system` | corresponding files | yes | varied/no direct audit calls | none identified by rg except examples | Not in required route list; active/experimental public module pages. | pages tests likely. |

## 5. FastAPI/Jinja Web Dashboard Audit

Audited `app/web/`, `app/web/routes_market.py`, `app/web/templates/`, and `app/web/static/`.

| Route | Implemented | Handler | Purpose/notes |
| --- | --- | --- | --- |
| `/market` | yes | `market_dashboard` | Main server-rendered Market Intelligence dashboard. |
| `/market-time-machine` | yes | `market_time_machine` | Alias for Market Time Machine. |
| `/market/time-machine` | yes | `market_time_machine` | Nested Market Time Machine route. |
| `/market/{section}` | yes | `market_section` | Dynamic market sections such as signals/evidence/narratives/sources if valid in template/controller logic. |
| `/intelligence/timeline` | yes | `market_timeline` | Server-rendered intelligence timeline. |
| `/evidence/{packet_id}` | yes | `evidence_viewer` | Server-rendered evidence packet view. |
| `/candles/{candle_id}` | yes | `candle_attribution_view` | Server-rendered candle attribution view. |
| `/web/market-time-machine` | yes | `web_market_time_machine_dto` | DTO endpoint for web dashboard. |
| `/web/timeline` | yes | `web_timeline_dto` | DTO endpoint. |
| `/web/candle/{candle_id}` | yes | `web_candle_dto` | DTO endpoint. |
| `/web/evidence/{packet_id}` | yes | `web_evidence_dto` | DTO endpoint. |
| `/web/market-time-machine/marker-click` | yes POST | `record_marker_click` | Analytics/event recording for web dashboard. |
| `/web/market-time-machine/candle-click` | yes POST | `record_candle_click` | Analytics/event recording. |
| `/web/market-time-machine/replay-open` | yes POST | `record_replay_open` | Analytics/event recording. |
| `/web/market-time-machine/evidence-view` | yes POST | `record_evidence_view` | Analytics/event recording. |

`/market` ownership is currently **FastAPI/Jinja** in the backend runtime. There is no Next.js `frontend/app/market/page.tsx` route in this checkout. Warning: Reflex migration must not take over `/market` without an explicit switch plan that preserves the existing FastAPI/Jinja dashboard or defines redirects/proxy ownership.

## 6. Frontend Navigation Audit

Audited `frontend/components/navigation/SiteHeader.tsx`, `frontend/components/interactive/BastionCommandPalette.tsx`, `frontend/components/layout/`, and `frontend/tests/navigation.test.tsx`.

### SiteHeader route presence

| Navigation item | Present | Current link/notes |
| --- | --- | --- |
| Platform | effectively yes | Link href `/platform`, but label uses `t.nav.products`; English renders `Products`, not `Platform`. |
| Trace | no | Missing from primary/mobile nav. |
| Evidence | yes | `/evidence`. |
| Status | yes | `/status` plus CTA. |
| Developers | yes | `/developers`. |
| Operations | effectively yes | Link href `/operations`, but label uses `t.nav.selfHost`; likely renders `Self-host`, not `Operations`. |
| Docs | yes | `/docs`. |
| Security | yes | `/security`. |
| Roadmap | yes | `/roadmap`. |
| Console | no | No console route found. |

### Command palette action presence

| Command | Present | Current link/notes |
| --- | --- | --- |
| Open Trace | no | Missing. |
| Check Bitcoin Address | no | Missing; `/check` exists. |
| Open Trace Report | no | Missing; dynamic route exists but needs input pattern. |
| Open Proof Packet | no | Missing; route exists but backend endpoint mismatch. |
| Open Evidence | partial | `View Evidence` links `/evidence`. |
| Open Status | partial | `View Status` links `/status`. |
| Open Console | no | No console route found. |
| Open Time Machine | no | Missing; FastAPI/Jinja route exists. |
| Open Sovereign Grid | no | Missing; `/products/sovereign-grid` exists but may be legacy. |

### Outdated/dead/legacy links

- Command palette links `/products` and `/self-host`; these routes currently exist, but they are outdated relative to new public IA assumptions (`/platform`, `/operations`) and should be cleaned up in Prompt 02 rather than deleted.
- SiteHeader labels are stale: `/platform` labeled Products, `/operations` labeled Self-host.
- `frontend/tests/navigation.test.tsx` expects `Products`, not `Platform` or Trace; tests should be updated with Prompt 02.

## 7. API Client Contract Audit

Audited `frontend/services/apiClient.ts`, `frontend/services/api.ts`, and `frontend/types/` plus call sites found by `rg`.

| Frontend method/call | HTTP path | Backend endpoint exists | Response envelope expected | Actual backend response shape | Mismatch | Required action |
| --- | --- | --- | --- | --- | --- | --- |
| `apiClient.getPublicLanding` | `/api/v1/public/landing` | yes | `ApiEnvelope<object>` | `ResponseEnvelope[PublicLandingResponse]` | Type too broad only. | Optional type tightening after contract freeze. |
| `apiClient.getPublicStatus` | `/api/v1/public/status` | yes | `ApiEnvelope<PublicStatusDTO>` | `ResponseEnvelope[PublicStatusResponse]` | Need confirm DTO field parity. | Contract test/type alignment prompt. |
| `apiClient.checkTraceLite` / `AddressCheckForm` | `/api/v1/trace/lite/{address}` | yes | `report_id` present | `ResponseEnvelope[dict[str, object]]` | Frontend type only requires `report_id`; backend dict may contain more fields. | Freeze minimum `{report_id}` or introduce typed schema. |
| `apiClient.getTraceSummary` / `apiGet` report page | `/api/v1/public/trace/{report_id}/summary` | yes | public Trace summary | `ResponseEnvelope[PublicTraceSummary]` | Works but split client usage (`apiClient` and `apiGet`). | Keep; consolidate later if needed. |
| `apiClient.getTraceReport` | `/api/v1/trace/report/{report_id}` | yes | object | `ResponseEnvelope[TraceReport]` | Type too broad. | Type with `TraceReport` if frontend uses full report. |
| `apiClient.getProofPacket` | `/api/v1/trace/report/{report_id}/proof-packet` | no | object | none; 404 | Hard mismatch. | Prompt 03 should either implement safe GET proof packet or update frontend to existing enterprise POST contract after design. |
| `apiClient.getTraceStatus` | `/api/v1/trace/status` | yes | object | `ResponseEnvelope[dict[str, object]]` | Type too broad. | Type once UI needs it. |
| `apiClient.getRuntimeEvents` | `/api/v1/trace/events` | yes | `RuntimeEventDTO[]` | `ResponseEnvelope[list[dict[str, object]]]` | Potential field-shape mismatch not proven. | Add contract test before WebSocket/event work. |
| `apiGet` generic | any supplied path | depends | assumes response has `.data` | backend mostly uses `ResponseEnvelope`, except auth and some evidence routes may differ | Broad helper hides response-shape mismatches. | Keep but add endpoint-specific contract tests. |

Priority mismatches: missing `/api/v1/trace/report/{report_id}/proof-packet`; Trace lite dict vs typed frontend minimum; Trace events runtime DTO shape should be frozen before event streams.

## 8. Event/Developer Layer Readiness Audit

| Feature | Current files/signals | Implemented | Safe to extend | Recommended future prompt |
| --- | --- | --- | --- | --- |
| Event bus | No dedicated event bus package found. Trace runtime events exist (`app/services/bastion_trace/trace_runtime_events.py` via service/router). | Partial operational records only. | No, not before taxonomy. | Prompt 04 — event taxonomy and registry. |
| Outbox | No clear outbox model/repository found. | No | No. | Add after taxonomy; design DB model and idempotency first. |
| Webhooks | `frontend/app/developers/webhooks/page.tsx` states contracts are not published; `BusinessCapability.WEBHOOK_PLACEHOLDER`; SIEM/webhook placeholders in docs. | No/placeholder. | No, not before outbox. | After outbox/delivery logs. |
| WebSocket | No WebSocket stream implementation found; Trace events are REST. | No | No. | After event taxonomy and REST event contract. |
| SDK | No root `sdk/` directory. | No | Not yet. | After public API schemas stabilize. |
| CLI | `app/cli/seed_news_sources.py`, `app/cli/seed_narratives.py`. | Internal seed scripts only. | Limited. | Public CLI after SDK and API contracts. |
| MCP | No `mcp/` directory or connector found. | No | Not yet. | After SDK/public API contract. |
| Plugin system | No plugin API foundation; unrelated build plugins only. | No | Not yet. | After MCP/SDK API boundary. |
| Delivery logs | `app/db/models/delivery.py`, `app/db/models/telegram.py`, `app/db/models/intelligence_signals.py`, signal delivery docs. | Partial/active for delivery observability. | Yes, carefully as read model; do not conflate with webhook delivery. | Outbox/delivery prompt. |
| Signal delivery logs | `/api/v1/signals/{signal_id}/delivery-logs` in `intelligence_signals.py`. | Yes for signals. | Yes with existing contract caution. | Signal event integration after taxonomy. |
| Audit log | `/api/v1/admin/audit-logs`; Trace immutable audit log service/docs. | Partial/baseline. | Yes if append-only semantics preserved. | Audit/event correlation prompt. |
| Runtime events | Trace runtime events/status endpoints and UI docs. | Partial Trace-specific baseline. | Yes as input to event taxonomy, not as final bus. | Prompt 04/05. |

Existing domains that should publish events later: signals, news, intelligence, onchain, Trace, wallet-health metadata, treasury request decisions, policy decisions, market data/provider health, observability/degraded state, evidence packets/replay, provider health, and operations/runtime readiness.

## 9. Deployment/Runtime Audit

| Item | Finding |
| --- | --- |
| Canonical Kubernetes path | `deploy/kubernetes/`. Makefile render/apply/run targets use `deploy/kubernetes/...`. |
| Legacy Kubernetes path | `k8s/` exists with base/jobs/observability/overlays/security. Deployment tests still reference it. |
| Existing canonical overlays | `deploy/kubernetes/overlays/dev`, `deploy/kubernetes/overlays/staging`, `deploy/kubernetes/overlays/production`. |
| Existing legacy overlays | `k8s/overlays/dev`, `k8s/overlays/staging`, `k8s/overlays/production`. |
| Missing canonical runtime overlays | `k3s`, `kind`, `minikube`, `single-node` are not present under `deploy/kubernetes/overlays/`. |
| Docker Compose | `docker-compose.yml` exists. No `docker-compose.*.yml` variants found in this audit pass. |
| Makefile targets | Includes Python test/lint/run/up/down/migration targets plus extensive `k8s-*` render/apply/evidence/security/operations/gitops/readiness targets. |
| Existing deployment tests | `tests/deployment/test_k8s_layout.py` references legacy `k8s/`; other tests reference `deploy/kubernetes`. |
| Path mismatch | Makefile canonicalizes `deploy/kubernetes`, while deployment layout tests require `k8s/`. |
| Missing runtime profiles | No explicit k3s/kind/minikube/single-node/bare-metal/systemd profiles found as first-class paths. |

Runtime plan implication: before adding new profiles, freeze `deploy/kubernetes` as canonical and decide whether `k8s/` remains compatibility fixture, legacy docs, or is migrated/test-updated.

## 10. Documentation Truthfulness Audit

| File | Section | Current claim | Actual repository state | Recommended correction | Future prompt |
| --- | --- | --- | --- | --- | --- |
| `docs/FINAL_PRODUCTION_GAP_AUDIT.md` | Bastion Trace gap addendum | “Website UI is pending.” | Next.js Trace routes/components/tests exist under `frontend/app/trace`, `frontend/app/check`, and `frontend/components/trace`. | Change to “Trace UI baseline exists; nav/API contract gaps remain.” | Prompt 03 or docs cleanup prompt. |
| `README.md` | Status/readiness/Kubernetes | Repeated RC-ready pending environment evidence language. | This is broadly truthful; cluster evidence remains pending. | Preserve cautious language; avoid strengthening to production-ready. | Runtime evidence prompts. |
| `docs/KUBERNETES_RC_CERTIFICATION.md` | Final Kubernetes audit classification | dev/staging/production overlays implemented; RC-ready pending evidence. | Matches `deploy/kubernetes/overlays`; does not cover k3s/kind/minikube/single-node profiles. | Add scope note that only dev/staging/production overlays exist. | Runtime profile prompt. |
| `docs/DEPLOYMENT_EVIDENCE_PACK.md` | Evidence workflow | Requires in-cluster evidence jobs/artifacts. | Canonical jobs/manifests exist; actual environment evidence not present in repo. | Preserve pending-evidence wording. | Evidence capture prompt. |
| `docs/PRODUCTION_READINESS.md` | Web dashboard/readiness sections | Web dashboard described as ready for operator review; production constraints listed. | FastAPI/Jinja dashboard exists; this is directionally true, but `/market` ownership should be explicit. | Add route ownership note before Reflex migration. | Frontend/runtime docs prompt. |
| `README.md` | Market dashboard | `/market` provides web intelligence console. | FastAPI/Jinja implements `/market`; no Next.js `/market`. | Clarify server-rendered FastAPI/Jinja ownership. | Prompt 02/market docs prompt. |
| Trace proof packet docs/UI | Various Trace docs/pages | Enterprise proof packets exist as evidence bundles; frontend has report proof-packet route. | Backend lacks `GET /api/v1/trace/report/{report_id}/proof-packet`; enterprise POST exists. | Distinguish enterprise proof-packet POST from public/report-scoped proof-packet GET. | Prompt 03. |
| Frontend docs/status | Various | Some historical claims say frontend/UI pending. | Public Next.js frontend is implemented; Trace UI baseline exists. | Replace pending with baseline/gaps. | Docs truthfulness prompt. |

## 11. No-Custody and Safety Audit

Searches were run for forbidden wording and sensitive input wording across repository paths excluding `node_modules`.

### Forbidden wording

No production UI/docs use of exact forbidden wording was found. Exact terms such as `clean address`, `dirty address`, `criminal address`, `guaranteed safe`, `approved payment`, and `verified illicit` appear in frontend tests and `frontend/lib/security.ts` as deny-list/test fixtures. This is acceptable and should be preserved.

| Location | Issue | Risk | Recommended action |
| --- | --- | --- | --- |
| `frontend/tests/*`, `frontend/lib/security.ts` | Forbidden terms appear as negative test/deny-list strings. | Low; these are guardrails. | Keep tests; ensure future UI copy does not render these terms. |

### Sensitive input acceptance / rejection

| Location | Issue | Risk | Recommended action |
| --- | --- | --- | --- |
| `app/services/bastion_trace/trace_service.py` | Rejects xprv/xpriv/.dat/seed phrase/mnemonic and 12+ words in Trace address input. | Low; guardrail exists. | Preserve and expand tests if adding new input surfaces. |
| `frontend/lib/addressValidation.ts` | Rejects xprv/tprv/xpriv, WIF-like input, 12+ words, and `.dat` in public address validation. | Low; guardrail exists. | Preserve. |
| `tests/integration/test_trace_api.py` and frontend tests | Validate xprv and seed/private key warnings. | Low; protective tests. | Keep. |
| Multiple docs/UI safety notices | Mention seed/private key handling as prohibited. | Low; positive safety language. | Preserve no-custody language. |
| Market intelligence keyword profiles/migrations | “private key leak”/“seed phrase” appear as news/narrative keywords. | Low/medium; not input acceptance, but content classification. | Keep context as news classification; do not turn into wallet input collection. |

No custody logic, seed/private key handling, wallet.dat upload, keystore handling, transaction signing, or signing-material collection should be introduced in future prompts.

## 12. Future 30-Prompt Dependency Map

- Prompt 02 depends on: this baseline audit; navigation/command palette route inventory; Trace visibility blockers.
- Prompt 03 depends on: Prompt 02 nav cleanup; Trace API mismatch list; proof-packet endpoint decision.
- Prompt 04 depends on: baseline router/domain inventory; no WebSocket/webhook implementation yet; event candidates list.
- Prompt 05 depends on: Prompt 04 event taxonomy/registry; existing runtime events/delivery logs inventory.
- Prompt 06 depends on: event taxonomy and outbox design; DB model/repository boundary decision.
- Prompt 07 depends on: outbox persistence and delivery log contract; webhook safety constraints.
- Prompt 08 depends on: outbox/webhook delivery contract; retry/idempotency rules.
- Prompt 09 depends on: event taxonomy and REST event contract; WebSocket must not precede these.
- Prompt 10 depends on: stable public API schemas; SDK package location decision.
- Prompt 11 depends on: SDK contracts; CLI public command contract; no-custody validation.
- Prompt 12 depends on: SDK/CLI API surfaces; MCP connector scope and auth boundaries.
- Prompt 13 depends on: MCP/API boundary; plugin API foundation constraints.
- Prompt 14 depends on: canonical deployment path decision (`deploy/kubernetes` vs `k8s`).
- Prompt 15 depends on: Prompt 14 path reconciliation; docker-compose baseline.
- Prompt 16 depends on: canonical runtime path; k3s overlay/profile design.
- Prompt 17 depends on: canonical runtime path; kind overlay/profile design.
- Prompt 18 depends on: canonical runtime path; minikube overlay/profile design.
- Prompt 19 depends on: single-node profile requirements and secrets/storage policy.
- Prompt 20 depends on: bare-metal/systemd boundaries; no production claims without evidence.
- Prompt 21 depends on: runtime profile docs and tests alignment.
- Prompt 22 depends on: Next.js route freeze and `/market` ownership warning; Reflex must be parallel only.
- Prompt 23 depends on: Reflex route inventory and API parity list.
- Prompt 24 depends on: Trace migration blocker resolved enough for Reflex parity.
- Prompt 25 depends on: Console shell scope; command palette cleanup; no primary frontend switch.
- Prompt 26 depends on: Reflex/Next.js route parity tests and API client contract alignment.
- Prompt 27 depends on: frontend parity evidence; migration switch plan drafted but not activated.
- Prompt 28 depends on: developer/API layer, runtime profiles, and Reflex parity all having explicit evidence.
- Prompt 29 depends on: docs truthfulness updates and release evidence artifacts.
- Prompt 30 depends on: final integration audit, complete verification, no-custody/safety re-scan, and no unsupported production-readiness claims.

## Verification Results

| Command | Result | Failure reason | Pre-existing or caused by this prompt |
| --- | --- | --- | --- |
| `python -m pytest -q` | Passed | 486 passed; 91 warnings (deprecations and duplicate OpenAPI operation ID warnings). | n/a |
| `make docs-truthfulness` | Passed | n/a | n/a |

## Immediate Blockers

- [ ] Trace is missing from `SiteHeader` primary/mobile navigation.
- [ ] SiteHeader labels are stale: `/platform` renders as Products and `/operations` renders as Self-host.
- [ ] Command Palette lacks Trace, Check Bitcoin Address, Trace Report, Proof Packet, Console, Time Machine, and Sovereign Grid actions.
- [ ] Command Palette still prioritizes outdated `/products` and `/self-host` routes instead of `/platform` and `/operations`.
- [ ] Frontend calls `/api/v1/trace/report/{report_id}/proof-packet`, but backend does not implement this GET endpoint.
- [ ] Deployment tests reference legacy `k8s/` while Makefile canonical targets use `deploy/kubernetes/`.
- [ ] Documentation says Trace Website UI is pending even though Trace UI baseline exists.

## Safe-To-Implement Next

- [ ] Prompt 02 — Trace navigation and command palette cleanup
- [ ] Prompt 03 — Trace API/frontend contract alignment
- [ ] Prompt 04 — Event taxonomy and registry

## Do-Not-Touch Yet

- [ ] Do not delete Next.js
- [ ] Do not replace `/market` ownership
- [ ] Do not introduce Reflex as primary frontend
- [ ] Do not add webhook delivery before outbox
- [ ] Do not add WebSocket streams before event taxonomy
- [ ] Do not claim production readiness without evidence

## Contract Freeze Summary

The current baseline is:

- Backend canonical source: FastAPI application under `app/`, with routers included from `app/main.py` under `/api/v1` plus root health and FastAPI/Jinja web routes.
- Public frontend currently: Next.js under `frontend/`.
- Market dashboard ownership: FastAPI/Jinja currently owns implemented `/market`; Next.js has no `/market` route in this checkout.
- Trace backend status: Active advisory baseline with public summary, lite, report, evidence, status, events, privacy/origin/counterparty/policy facets; not production-calibrated; missing report-scoped proof-packet GET.
- Trace frontend status: Next.js Trace/check/report/proof-packet baseline exists, but primary nav/command palette exposure and proof-packet API contract need fixes.
- Deployment canonical path: `deploy/kubernetes/`.
- Known legacy paths: `k8s/` remains present and referenced by `tests/deployment/test_k8s_layout.py`; `/products` and `/self-host` frontend route trees remain implemented but are stale relative to `/platform` and `/operations` IA.
- Next prompt: Prompt 02 — Trace navigation and command palette cleanup.
