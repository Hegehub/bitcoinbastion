# Frontend Route Inventory

Date: 2026-06-19  
Status labels: `implemented`, `partial`, `missing`, `stale`, `unknown`, `delegated-to-fastapi-jinja`, `blocked`.  
Migration priority labels: `P0 — must migrate before cutover`, `P1 — should migrate before cutover`, `P2 — can migrate after initial Reflex launch`, `Delegated — intentionally owned by non-Reflex surface`.

## Inventory notes

- Current Next.js dynamic route naming uses `[reportId]`; the proposed Reflex route uses `[report_id]`.
- Current Market routes are implemented by FastAPI/Jinja, not by Next.js.
- Current `/console/*` targets are missing from Next.js and are not registered in the inspected Reflex app.
- `/web/*` entries are DTO/action endpoints, not browser pages; they are included because Market and Time Machine parity depends on them.

| Route | Current owner | Implementation path | Current status | Backend dependency | Should Reflex own it? | Migration priority | Blocking issues | Safety notes |
|---|---|---|---|---|---:|---|---|---|
| / | Next.js | frontend/app/page.tsx | implemented | /api/v1/public/landing; /api/v1/public/status | True | P1 — should migrate before cutover | Preserve fallback/stale visibility. | Advisory/no-custody copy visible. |
| /platform | Next.js | frontend/app/platform/page.tsx | implemented | public status/features optional | True | P1 — should migrate before cutover | Content parity needed. | Avoid production-readiness overclaims. |
| /developers | Next.js | frontend/app/developers/page.tsx | implemented | public API docs/examples | True | P1 — should migrate before cutover | Subroutes need mapping or redirects. | API examples must unwrap ResponseEnvelope.data. |
| /operations | Next.js | frontend/app/operations/page.tsx | implemented | operations/status optional | True | P2 — can migrate after initial Reflex launch | Must preserve operator/degraded visibility. | No custody; degraded states visible. |
| /manifesto | Next.js | frontend/app/manifesto/page.tsx | implemented | none | True | P2 — can migrate after initial Reflex launch | Legacy links may need disposition. | No signing/custody claims. |
| /evidence | Next.js | frontend/app/evidence/page.tsx | implemented | evidence/public stats optional | True | P1 — should migrate before cutover | Distinguish public evidence from Market evidence packet route. | Not legal proof; limitations visible. |
| /status | Next.js | frontend/app/status/page.tsx | implemented | /api/v1/public/status | True | P1 — should migrate before cutover | Must preserve fallback/stale states. | Degraded/stale visible. |
| /roadmap | Next.js | frontend/app/roadmap/page.tsx | implemented | /api/v1/public/roadmap optional | True | P2 — can migrate after initial Reflex launch | Avoid contradicting readiness docs. | No parity overclaim. |
| /security | Next.js | frontend/app/security/page.tsx | implemented | none | True | P1 — should migrate before cutover | Must preserve no-sensitive-input warnings. | No seed/private key/wallet-file handling. |
| /docs | Next.js | frontend/app/docs/page.tsx | implemented | OpenAPI/docs links | True | P2 — can migrate after initial Reflex launch | Keep API path examples accurate. | Advisory/no-custody limits visible. |
| /check | Next.js | frontend/app/check/page.tsx | implemented | /api/v1/trace/lite/{address} | True | P0 — must migrate before cutover | Trace blocker; input validation parity required. | Public addresses only; no sensitive wallet material. |
| /trace | Next.js | frontend/app/trace/page.tsx | implemented | /api/v1/trace/lite/{address} | True | P0 — must migrate before cutover | Alias must continue to work. | Same as /check. |
| /trace/[report_id] | Next.js actual /trace/[reportId] | frontend/app/trace/[reportId]/page.tsx | implemented | /api/v1/public/trace/{report_id}/summary; /api/v1/trace/report/{report_id} | True | P0 — must migrate before cutover | Dynamic param naming differs from target Reflex route. | Advisory limitations and unavailable states visible. |
| /trace/[report_id]/proof-packet | Next.js actual /trace/[reportId]/proof-packet | frontend/app/trace/[reportId]/proof-packet/page.tsx | implemented | /api/v1/trace/report/{report_id}/proof-packet | True | P0 — must migrate before cutover | Proof Packet route must keep unavailable state. | Not legal proof; redaction/integrity limitations visible. |
| /console | Missing in Next.js and Reflex route registration | No frontend/app/console/page.tsx; reflex routes dir has no page module | missing | console/status APIs TBD | True | P1 — should migrate before cutover | Target route absent; legacy Next.js /dashboard exists. | Read-only/operator-review posture. |
| /console/trace | Missing in Next.js and Reflex route registration | none | missing | /api/v1/trace/status; /api/v1/trace/events | True | P1 — should migrate before cutover | Target route absent. | Advisory/read-only. |
| /console/evidence | Missing in Next.js and Reflex route registration | none | missing | evidence APIs TBD | True | P2 — can migrate after initial Reflex launch | Target route absent. | Not legal proof. |
| /console/market-intelligence | Missing in Next.js and Reflex route registration | none | missing | Market DTO/API endpoints | True | P1 — should migrate before cutover | Command palette currently points to /market. | Stale/fallback states visible. |
| /console/time-machine | Missing in Next.js and Reflex route registration | none | missing | /web/market-time-machine | True | P1 — should migrate before cutover | Command palette currently points to /market/time-machine. | Market limitations visible. |
| /console/sovereign-grid | Missing in Next.js and Reflex route registration | none | missing | TBD | True | P2 — can migrate after initial Reflex launch | Target route absent. | Read-only/no custody. |
| /console/policy | Missing in Next.js and Reflex route registration | none | missing | policy APIs | True | P2 — can migrate after initial Reflex launch | Target route absent. | Advisory/operator review. |
| /console/audit | Missing in Next.js and Reflex route registration | none | missing | audit/observability APIs | True | P2 — can migrate after initial Reflex launch | Target route absent. | Evidence-based; degraded visible. |
| /market | FastAPI/Jinja | app/web/routes_market.py; app/web/templates/market/dashboard.html | delegated-to-fastapi-jinja | /web/market-time-machine; service dashboard | True | P1 — should migrate before cutover | Ownership split; keep Jinja until parity. | Market limitations and stale data visible. |
| /market/timeline | FastAPI/Jinja via /market/{section} | app/web/routes_market.py | delegated-to-fastapi-jinja | /web/timeline; service timeline | True | P1 — should migrate before cutover | Section route handles timeline. | Limitations visible. |
| /market/time-machine | FastAPI/Jinja | app/web/routes_market.py; templates/market/time_machine.html | delegated-to-fastapi-jinja | /web/market-time-machine | True | P1 — should migrate before cutover | Must not break current dashboard. | Limitations visible. |
| /market/signals | FastAPI/Jinja via /market/{section} | app/web/routes_market.py | delegated-to-fastapi-jinja | service view model | True | P2 — can migrate after initial Reflex launch | Section route handles signals. | Advisory-only signals. |
| /market/evidence | FastAPI/Jinja via /market/{section} | app/web/routes_market.py | delegated-to-fastapi-jinja | service view model | True | P2 — can migrate after initial Reflex launch | Distinct from public /evidence. | Not legal proof. |
| /market/narratives | FastAPI/Jinja via /market/{section} | app/web/routes_market.py | delegated-to-fastapi-jinja | service view model | True | P2 — can migrate after initial Reflex launch | Section route handles narratives. | Source limitations visible. |
| /market/sources | FastAPI/Jinja via /market/{section} | app/web/routes_market.py | delegated-to-fastapi-jinja | source summary | True | P2 — can migrate after initial Reflex launch | Section route handles sources. | Provider health/staleness visible. |
| /intelligence/timeline | FastAPI/Jinja | app/web/routes_market.py; templates/market_timeline.html | delegated-to-fastapi-jinja | /web/timeline; service timeline | False | Delegated — intentionally owned by non-Reflex surface | Legacy/current route must not disappear silently. | Limitations visible. |
| /evidence/{packet_id} | FastAPI/Jinja | app/web/routes_market.py; templates/evidence_viewer.html | delegated-to-fastapi-jinja | /web/evidence/{packet_id} | False | Delegated — intentionally owned by non-Reflex surface | Route overlaps conceptually with public /evidence. | Not legal proof; unavailable state. |
| /candles/{candle_id} | FastAPI/Jinja | app/web/routes_market.py; templates/candle_attribution.html | delegated-to-fastapi-jinja | /web/candle/{candle_id} | False | Delegated — intentionally owned by non-Reflex surface | Market detail route. | Attribution limitations. |
| /web/market-time-machine | FastAPI DTO | app/web/routes_market.py | implemented | MarketTimeMachineWebService.dashboard() | False | Delegated — intentionally owned by non-Reflex surface | Not a page route. | DTO must expose limitations/unavailable data. |
| /web/timeline | FastAPI DTO | app/web/routes_market.py | implemented | MarketTimeMachineWebService.timeline() | False | Delegated — intentionally owned by non-Reflex surface | Not a page route. | DTO must expose limitations. |
| /web/candle/{candle_id} | FastAPI DTO | app/web/routes_market.py | implemented | MarketTimeMachineWebService.candle_attribution() | False | Delegated — intentionally owned by non-Reflex surface | Not a page route. | Numeric-only id. |
| /web/evidence/{packet_id} | FastAPI DTO | app/web/routes_market.py | implemented | MarketTimeMachineWebService.evidence_panel() | False | Delegated — intentionally owned by non-Reflex surface | Not a page route. | Not legal proof; numeric-only id. |

## Additional current Next.js routes outside target list

These routes exist in `frontend/app/` but are not required target Reflex routes for the initial cutover: `/blog`, `/blog/[slug]`, `/citadel`, `/dashboard`, `/dashboard/*`, `/design-system`, `/enterprise`, `/genesis`, `/products`, `/products/*`, `/register`, `/self-host`, `/self-host/*`, `/trace/business*`, `/trace/enterprise*`, and `/treasury`.

Status: treat as `stale`, `partial`, or legacy-supported until a later archive/redirect prompt decides their fate. Do not delete them in this freeze prompt.
