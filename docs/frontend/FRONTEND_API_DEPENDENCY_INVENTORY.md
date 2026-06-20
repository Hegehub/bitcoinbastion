# Frontend API Dependency Inventory

Date: 2026-06-19  
Scope: current Next.js frontend clients/examples, FastAPI routers, and FastAPI/Jinja Market DTO endpoints.

## Status and mismatch labels

- Current status: `implemented`, `partial`, `missing`, `unused-by-frontend`, `delegated-to-fastapi-jinja`, `unknown`.
- Mismatch values: `no`, `frontend-calls-missing-backend-endpoint`, `backend-available-unused-by-frontend`, `route-shape-mismatch`, `ownership-mismatch`.

## API dependency table

| Frontend route/component | Frontend service/client | HTTP method | API endpoint | Backend implementation path | Response model / DTO if known | Current status | Mismatch? | Recommended action |
|---|---|---:|---|---|---|---|---|---|
| Home/public pages | frontend/services/apiClient.ts:getPublicLanding; frontend/lib/api/public.ts:getLanding | GET | /api/v1/public/landing | app/api/v1/public.py | ResponseEnvelope[PublicLandingResponse] | implemented | no | Preserve in Reflex public client. |
| Status page/header/footer | getPublicStatus; frontend/lib/api/public.ts:getStatus | GET | /api/v1/public/status | app/api/v1/public.py | ResponseEnvelope[PublicStatusResponse] | implemented | no | Preserve with stale/fallback state. |
| Roadmap page/docs examples | frontend/lib/api/public.ts:getRoadmap; developer examples | GET | /api/v1/public/roadmap | app/api/v1/public.py | ResponseEnvelope[PublicRoadmapResponse] | implemented | no | Preserve in Reflex roadmap client. |
| Public stats/evidence modules | frontend/lib/api/public.ts:getStats | GET | /api/v1/public/stats | app/api/v1/public.py | ResponseEnvelope[PublicStatsResponse] | implemented | no | Preserve if Reflex public stats render live data. |
| Public feature grid/docs examples | frontend/lib/api/public.ts:getFeatures | GET | /api/v1/public/features | app/api/v1/public.py | ResponseEnvelope[list[PublicFeatureEntry]] | implemented | no | Preserve for feature catalog. |
| /check, /trace, report preview | apiClient.getTraceSummary | GET | /api/v1/public/trace/{report_id}/summary | app/api/v1/public.py | ResponseEnvelope[PublicTraceSummary] | implemented | no | Required for Reflex Trace Lite flow. |
| /check, /trace | apiClient.checkTraceLite | GET | /api/v1/trace/lite/{address} | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Required P0; preserve address encoding/validation. |
| Full address report workflow | none in current Next.js client | GET | /api/v1/trace/address/{address} | app/api/v1/trace.py | ResponseEnvelope[TraceReport] | implemented | backend-available-unused-by-frontend | Add Reflex service only if full address report UX needs it. |
| Trace report page | apiClient.getTraceReport | GET | /api/v1/trace/report/{report_id} | app/api/v1/trace.py | ResponseEnvelope[TraceReport] | implemented | no | Use for Reflex full report route. |
| Trace report evidence panel | apiClient.getTraceEvidence | GET | /api/v1/trace/report/{report_id}/evidence | app/api/v1/trace.py | ResponseEnvelope[list[TraceEvidence]] | implemented | no | Preserve with unavailable state. |
| Trace privacy panel | apiClient.getTracePrivacyShield | GET | /api/v1/trace/report/{report_id}/privacy-shield | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Preserve with fallback panel. |
| Trace origin panel | apiClient.getTraceOriginPassport | GET | /api/v1/trace/report/{report_id}/origin-passport | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Preserve with fallback panel. |
| Trace source summary panel | none in current Next.js client | GET | /api/v1/trace/report/{report_id}/source-summary | app/api/v1/trace.py | ResponseEnvelope[list[dict]] | implemented | backend-available-unused-by-frontend | Add Reflex service/panel or document omission. |
| Trace provider disagreement panel | apiClient.getTraceProviderDisagreement | GET | /api/v1/trace/report/{report_id}/provider-disagreement | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Preserve and keep disagreement visible. |
| Trace UTXO hygiene panel | none in current Next.js client | GET | /api/v1/trace/report/{report_id}/utxo-hygiene | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | backend-available-unused-by-frontend | Add Reflex service/panel or document omission. |
| Trace dust radar panel | none in current Next.js client | GET | /api/v1/trace/report/{report_id}/dust-radar | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | backend-available-unused-by-frontend | Add Reflex service/panel or document omission. |
| Trace counterparty panel | apiClient.getTraceCounterpartyLens | GET | /api/v1/trace/report/{report_id}/counterparty-lens | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Preserve with fallback panel. |
| Payment context requested shape | none; prompt expected report-scoped endpoint | POST | /api/v1/trace/report/{report_id}/payment-context | Backend actual: app/api/v1/trace.py has /api/v1/trace/payment-context | ResponseEnvelope[dict] | partial | route-shape-mismatch | Decide whether to add report-scoped backend route or update frontend expectation. |
| Payment intent preview requested shape | none; prompt expected report-scoped endpoint | POST | /api/v1/trace/report/{report_id}/payment-intent/preview | Backend actual: app/api/v1/trace.py has /api/v1/trace/payment-intent/preview | ResponseEnvelope[dict] | partial | route-shape-mismatch | Decide whether report id belongs in payload or route. |
| Destination review requested shape | none; prompt expected report-scoped endpoint | POST | /api/v1/trace/report/{report_id}/destination-review | Backend actual: app/api/v1/trace.py has /api/v1/trace/destination-review | ResponseEnvelope[dict] | partial | route-shape-mismatch | Align route contract before Reflex uses it. |
| Trace policy facts panel | apiClient.getTracePolicyFacts | GET | /api/v1/trace/report/{report_id}/policy-facts | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Preserve with operator-review framing. |
| Proof Packet page | apiClient.getProofPacket | GET | /api/v1/trace/report/{report_id}/proof-packet | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Required P0; not legal proof. |
| Trace status/console | apiClient.getTraceStatus | GET | /api/v1/trace/status | app/api/v1/trace.py | ResponseEnvelope[dict] | implemented | no | Required for status/console parity. |
| Trace runtime events/console | apiClient.getTraceEvents; getRuntimeEvents | GET | /api/v1/trace/events | app/api/v1/trace.py | ResponseEnvelope[list[dict]] | implemented | no | Preserve with degraded state. |
| Market public/console future | none in Next.js primary client | GET | /api/v1/market/* | app/api/v1/market.py and app/api/v1/market_data.py | market price/provider/candle dict DTOs | implemented | backend-available-unused-by-frontend | Reflex Market client may use or continue /web/* mirror; note duplicate router prefix. |
| Market data requested group | none in Next.js primary client | GET | /api/v1/market-data/* | Actual router prefix is /api/v1/market in app/api/v1/market_data.py | market data dict DTOs | partial | route-shape-mismatch | Document actual prefix; avoid inventing /market-data calls. |
| Market intelligence requested group | none in Next.js primary client | GET | /api/v1/market-intelligence/* | Actual router prefix is /api/v1/news in app/api/v1/market_intelligence.py | news/source/event DTOs | partial | route-shape-mismatch | Document actual /api/v1/news/* paths or add alias later. |
| Intelligence timeline requested group | none in Next.js primary client | GET | /api/v1/intelligence-timeline/* | Actual router prefix is /api/v1/intelligence/timeline in app/api/v1/intelligence_timeline.py | timeline DTOs | partial | route-shape-mismatch | Use actual path or add compatibility alias later. |
| Signals future | none in Next.js primary client | GET | /api/v1/signals/* | app/api/v1/signals.py and app/api/v1/intelligence_signals.py | signal DTOs/envelopes or dicts | implemented | backend-available-unused-by-frontend | Use carefully; two routers share /signals prefix. |
| Onchain future | none in Next.js primary client | GET | /api/v1/onchain/* | app/api/v1/onchain.py via app/main.py | onchain DTOs | implemented | backend-available-unused-by-frontend | Include only if Reflex route needs onchain data. |
| Market dashboard | Jinja/Reflex future market client | GET | /web/market-time-machine | app/web/routes_market.py | MarketTimelineDTO + view model dict | implemented | no | Preserve/delegate during Reflex parity. |
| Market timeline | Jinja/Reflex future market client | GET | /web/timeline | app/web/routes_market.py | timeline DTO dict | implemented | no | Preserve/delegate during Reflex parity. |
| Candle detail | Jinja/Reflex future market client | GET | /web/candle/{candle_id} | app/web/routes_market.py | candle attribution DTO dict | implemented | no | Numeric-only id; preserve limitations. |
| Evidence packet detail | Jinja/Reflex future market client | GET | /web/evidence/{packet_id} | app/web/routes_market.py | evidence panel DTO dict | implemented | no | Numeric-only id; not legal proof. |

## Frontend API client behavior

- `frontend/services/api.ts` and `frontend/services/apiClient.ts` unwrap `body.data` or `j.data` when present.
- `frontend/lib/api/client.ts` exposes `fetchEnvelope<T>()` for public API calls and returns fallback data when provided.
- Reflex API clients must preserve `ResponseEnvelope.data` unwrapping, timeout handling, backend error normalization, raw `/web/*` DTO support, and visible fallback/error states.
