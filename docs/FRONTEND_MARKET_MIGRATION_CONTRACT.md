# Frontend Market Migration Contract

Date: 2026-06-22  
Status: audit contract only. No route ownership changed.

## 1. Executive summary

Bitcoin Bastion already has an active FastAPI/Jinja Market Intelligence and Market Time Machine surface. Reflex must not take over `/market` until it can preserve the current dashboard contract: Time Machine charting, candle drilldowns, evidence packet links, replay links, signal and narrative panels, provider-health visibility, safety limitations, and degraded/empty/error states.

Current decision: **FastAPI/Jinja remains canonical for Market routes through Prompt 10**. Future Reflex work should mirror and then own selected routes only after DTO parity and safety-copy parity are demonstrated.

Inspected required paths:

| Path | Status | Notes |
|---|---:|---|
| `app/main.py` | present | Includes API routers under `settings.api_prefix` and includes `market_time_machine_web_router` without API prefix. |
| `app/web/` | present | Owns the current web dashboard, templates, static JS/CSS, metrics, view model, and web service. |
| `app/web/routes_market.py` | present | Canonical web route and DTO owner for Market dashboard/Time Machine/timeline/evidence/candle pages. |
| `app/api/v1/market.py` | present | BTC market API with overlapping `/api/v1/market/*` paths. |
| `app/api/v1/market_data.py` | present | Also mounted under `/api/v1/market`; overlaps with `market.py` for several BTC paths. |
| `app/api/v1/market_intelligence.py` | present | Mounted under `/api/v1/news`; source/event APIs. |
| `app/api/v1/intelligence_timeline.py` | present | Mounted under `/api/v1/intelligence/timeline`; timeline APIs. |
| `app/api/v1/intelligence.py` | present | Mounted under `/api/v1/intelligence`; similarity, narrative, candle, evidence-related DTOs. |
| `app/api/v1/intelligence_signals.py` | present | Mounted under `/api/v1/signals`; signal governance/public signal endpoints. |
| `app/api/v1/signals.py` | present | Also mounted under `/api/v1/signals`; ResponseEnvelope signal endpoints. |
| `app/api/v1/evidence.py` | present | Evidence packet/replay APIs under `/api/v1/evidence`. |
| `app/api/v1/provider_health.py` | missing | Provider health is exposed via other routers/services, not this path. |
| `app/api/v1/observability.py` | present | Operations snapshot endpoint. |
| `frontend/` | present | Legacy Next.js has command-palette references to Market routes, but no full Market page implementation. |
| `docs/MARKET*.md`, `docs/*TIME_MACHINE*.md`, `docs/*INTELLIGENCE*.md` | present | Multiple docs define limitations and market intelligence behavior. |

## 2. Current market surfaces

| Surface name | Path | Type | Status | Current owner | Future Reflex owner | Migration risk | Notes |
|---|---|---|---|---|---|---|---|
| Market Intelligence dashboard | `/market` | FastAPI route + Jinja | active | `app/web/routes_market.py` | Reflex should eventually own primary route after parity | BLOCKER | Renders `market/dashboard.html` and `components/market_panels.html`. |
| Legacy Time Machine alias | `/market-time-machine` | FastAPI route + Jinja | active alias | `app/web/routes_market.py` | Keep as alias during parity | HIGH | Alias points to the same `market_time_machine` handler as `/market/time-machine`. |
| Market Time Machine | `/market/time-machine` | FastAPI route + Jinja | active | `app/web/routes_market.py` | Reflex should mirror first, own later | BLOCKER | Uses `market/time_machine.html`, chart JS, candle/evidence panels. |
| Market sections | `/market/{section}` | FastAPI route + Jinja | active dynamic | `app/web/routes_market.py` | Reflex should own static equivalents later | HIGH | Supports timeline, time-machine, signals, evidence, narratives, sources; legacy aliases normalize candles/events/news/shock-index. |
| Intelligence timeline | `/intelligence/timeline` | FastAPI route + Jinja | active | `app/web/routes_market.py` | Likely remain alias or API-backed Reflex route | HIGH | Uses `market_timeline.html`, filters, pagination, evidence/candle links. |
| Evidence viewer | `/evidence/{packet_id}` | FastAPI route + Jinja | active | `app/web/routes_market.py` | Reflex may own later after Evidence parity | HIGH | Renders `evidence_viewer.html`; must preserve replay and limitations. |
| Candle attribution | `/candles/{candle_id}` | FastAPI route + Jinja | active | `app/web/routes_market.py` | Reflex may own later | HIGH | Renders `candle_attribution.html`; must preserve candidate events and replay status. |
| Web Time Machine DTO | `/web/market-time-machine` | DTO endpoint | active | `app/web/routes_market.py` | Reflex should call via client initially | BLOCKER | Returns chart, timeline, candle, marker, limitations, and view-model fields. |
| Web timeline DTO | `/web/timeline` | DTO endpoint | active | `app/web/routes_market.py` | Reflex should call via client initially | HIGH | Returns `MarketTimelineDTO.model_dump()` or empty/degraded payload. |
| Web candle DTO | `/web/candle/{candle_id}` | DTO endpoint | active | `app/web/routes_market.py` | Reflex should call via client initially | HIGH | Returns `CandleAttributionDTO.model_dump()` or degraded payload. |
| Web evidence DTO | `/web/evidence/{packet_id}` | DTO endpoint | active | `app/web/routes_market.py` | Reflex should call via client initially | HIGH | Returns `EvidencePanelDTO.model_dump()` or degraded payload. |
| Metric POST endpoints | `/web/market-time-machine/*` | tracking endpoints | active | `app/web/routes_market.py` | Backend-only or optional Reflex telemetry client | MEDIUM | Records marker/candle/replay/evidence interactions; not domain logic. |
| Legacy Next.js command palette | `frontend/components/interactive/BastionCommandPalette.tsx` | React component | active legacy | Next.js | Reflex registry already has canonical actions | MEDIUM | Points to `/market`, `/market/timeline`, `/market/time-machine`, `/market/signals`, `/market/evidence`, `/market/narratives`, `/market/sources`. |

## 3. Current route inventory

| Route | Current Owner | Current Path | Response Type | Template/component used | Backend service dependency | DTO/API dependency | Future Reflex Route | Keep Alias? | Priority | Safety requirements | Blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `/market` | FastAPI/Jinja | `app/web/routes_market.py::market_dashboard` | HTML | `app/web/templates/market/dashboard.html` | `MarketTimeMachineWebService.dashboard`, `landing_payload`, `source_summary`; `build_market_dto` | `/web/market-time-machine` equivalent DTO | `/market` | no after cutover, yes during parity | P0 | not financial advice, correlation limitations, provider health visible | Reflex must reproduce full dashboard cards/chart/evidence/provider panels. |
| `/market-time-machine` | FastAPI/Jinja | `market_time_machine` alias | HTML | `app/web/templates/market/time_machine.html` | same as `/market/time-machine` | `/web/market-time-machine` | `/market/time-machine` | yes as legacy alias | P1 | limitations visible | Alias behavior must be documented in Reflex router/proxy. |
| `/market/time-machine` | FastAPI/Jinja | `market_time_machine` | HTML | `app/web/templates/market/time_machine.html` | dashboard + Time Machine view model | `/web/market-time-machine` | `/market/time-machine` | no after Reflex owns | P0 | degraded, stale, evidence limitations | Chart/candle/evidence interactions must be preserved. |
| `/market/timeline` | FastAPI/Jinja | `market_section(section='timeline')` | HTML | `app/web/templates/market/section.html` | dashboard context + timeline frame | `/web/timeline` and `/web/market-time-machine` | `/market/timeline` | no after Reflex owns | P1 | limitations visible | Dynamic section currently shares one template. |
| `/market/signals` | FastAPI/Jinja | `market_section(section='signals')` | HTML | `market/section.html` + `signals_view` macro | `signal_summary` | `/api/v1/signals/*`, `/web/market-time-machine` | `/market/signals` | no after Reflex owns | P1 | no trading instruction, operator review visible | Signal router overlap must be resolved. |
| `/market/evidence` | FastAPI/Jinja | `market_section(section='evidence')` | HTML | `market/section.html` + `evidence_view` macro | `evidence_summary`, `replay_requests_summary` | `/web/evidence/{packet_id}`, `/api/v1/evidence/*` | `/market/evidence` | no after Reflex owns | P1 | evidence limitations visible | Evidence packet ID mapping must be preserved. |
| `/market/narratives` | FastAPI/Jinja | `market_section(section='narratives')` | HTML | `market/section.html` + `narrative_summary` macro | `narrative_panel` | `/api/v1/intelligence/narratives*` | `/market/narratives` | no after Reflex owns | P2 | historical context only | Narrative API shape differs from view model. |
| `/market/sources` | FastAPI/Jinja | `market_section(section='sources')` | HTML | `market/section.html` + `sources_view` macro | `source_summary` | `/api/v1/news/sources*` | `/market/sources` | no after Reflex owns | P2 | source health visible | Need source/provider matrix parity. |
| `/market/{section}` | FastAPI/Jinja | `market_section` | HTML | `market/section.html` | section-specific view model frame | mixed | static Reflex routes | maybe for legacy section aliases | P2 | section limitations | Legacy aliases `candles`, `events`, `news`, `shock-index` need redirect/alias plan. |
| `/intelligence/timeline` | FastAPI/Jinja | `market_timeline` | HTML | `market_timeline.html` | `MarketTimeMachineWebService.timeline` | `/web/timeline`, `/api/v1/intelligence/timeline*` | `/market/timeline` or `/intelligence/timeline` | yes during parity | P1 | filters not advice | Route name differs from target Reflex market route. |
| `/evidence/{packet_id}` | FastAPI/Jinja | `evidence_viewer` | HTML | `evidence_viewer.html` | `evidence_panel`, `replay_summary` | `/web/evidence/{packet_id}`, `/api/v1/evidence/packets/{packet_id}` | `/market/evidence` or `/evidence/{packet_id}` | yes during parity | P1 | evidence not proof of causation | Do not break Trace Proof Packet work. |
| `/candles/{candle_id}` | FastAPI/Jinja | `candle_attribution_view` | HTML | `candle_attribution.html` | `candle_attribution` | `/web/candle/{candle_id}`, `/api/v1/intelligence/candles/{candle_id}` | `/market/time-machine` detail | yes during parity | P1 | correlation limitations | Reflex must preserve candle drilldown. |
| `/web/market-time-machine` | FastAPI web DTO | `web_market_time_machine_dto` | JSON | N/A | `dashboard`, `landing_payload`, `build_market_dto` | canonical DTO | Backend API-only | yes | P0 | limitations included | DTO contains merged schema; Reflex client needs typed adapter. |
| `/web/timeline` | FastAPI web DTO | `web_timeline_dto` | JSON | N/A | `timeline` | canonical DTO | Backend API-only | yes | P1 | limitations included | Filter/window semantics must match UI. |
| `/web/candle/{candle_id}` | FastAPI web DTO | `web_candle_dto` | JSON | N/A | `candle_attribution` | canonical DTO | Backend API-only | yes | P1 | limitations included | Missing candle returns degraded payload. |
| `/web/evidence/{packet_id}` | FastAPI web DTO | `web_evidence_dto` | JSON | N/A | `evidence_panel` | canonical DTO | Backend API-only | yes | P1 | limitations included | Missing evidence returns degraded payload. |

## 4. Current DTO/API endpoint inventory

| Endpoint | Method | Current implementation path | Response shape | Consumer | Used by route | Error/empty/degraded behavior | Should Reflex call directly? | Needs wrapper/client? |
|---|---|---|---|---|---|---|---|---|
| `/web/market-time-machine` | GET | `routes_market.py::web_market_time_machine_dto` | merged `MarketTimelineDTO` + `market_vm` dict | Future JS/Reflex DTO client; tests | `/market`, `/market/time-machine` equivalent | OperationalError returns empty chart/timeline/candles plus limitations including data unavailable | yes initially | `market_time_machine_client.get_dashboard` |
| `/web/timeline` | GET | `routes_market.py::web_timeline_dto` | `MarketTimelineDTO.model_dump()` | Timeline clients | `/intelligence/timeline` equivalent | OperationalError returns empty timeline and limitations | yes initially | `market_time_machine_client.get_timeline` |
| `/web/candle/{candle_id}` | GET | `routes_market.py::web_candle_dto` | `CandleAttributionDTO.model_dump()` | Candle detail | `/candles/{candle_id}` | OperationalError returns id + limitations | yes initially | `market_time_machine_client.get_candle` |
| `/web/evidence/{packet_id}` | GET | `routes_market.py::web_evidence_dto` | `EvidencePanelDTO.model_dump()` | Evidence panel | `/evidence/{packet_id}` | OperationalError returns packet_id + limitations | yes initially | `market_time_machine_client.get_evidence` |
| `/web/market-time-machine/marker-click` | POST | `routes_market.py::record_marker_click` | `{status: recorded}` | `app/web/static/js/market.js` | chart marker interactions | fire-and-forget metrics | optional | telemetry client only |
| `/web/market-time-machine/candle-click` | POST | `record_candle_click` | `{status: recorded}` | `market.js` | chart candle interactions | fire-and-forget metrics | optional | telemetry client only |
| `/web/market-time-machine/replay-open` | POST | `record_replay_open` | `{status: recorded}` | `market.js` | replay link clicks | fire-and-forget metrics | optional | telemetry client only |
| `/web/market-time-machine/evidence-view` | POST | `record_evidence_view` | `{status: recorded}` | `market.js` | evidence link clicks | fire-and-forget metrics | optional | telemetry client only |
| `/api/v1/market/btc/price` | GET | `market.py`, `market_data.py` | BTC price payload | API consumers | not current Jinja | provider unavailable payloads vary | maybe | consolidate overlap |
| `/api/v1/market/btc/providers` | GET | `market.py`, `market_data.py` | provider list | API consumers | not current Jinja | provider payloads | maybe | provider-health client |
| `/api/v1/market/providers/health` | GET | `market.py` | market health snapshot | API consumers | not current Jinja | degraded source info | yes later | provider-health client |
| `/api/v1/market/btc/providers/health` | GET | `market_data.py` | provider health | API consumers | not current Jinja | overlaps with above | maybe | resolve overlap |
| `/api/v1/market/btc/candles*` | GET | `market.py` | candle history/latest/id/evidence | API consumers | not current Jinja | limitations by endpoint | maybe | market data client |
| `/api/v1/market/health` | GET | `market.py` | health status | API consumers | not current Jinja | health payload | yes | provider-health client |
| `/api/v1/news/sources*` | GET | `market_intelligence.py` | source registry/health/snapshots/confidence/events | API consumers | sources panel equivalent | not current Jinja direct | yes later | intelligence client |
| `/api/v1/news/events*` | GET | `market_intelligence.py` | event list/detail/articles/high-impact/security/regulatory | API consumers | event/timeline equivalent | not current Jinja direct | yes later | intelligence client |
| `/api/v1/intelligence/timeline*` | GET | `intelligence_timeline.py` | timeline/latest/window/context/narratives/impacts/day/hour | API consumers | timeline equivalent | not current Jinja direct | yes later | intelligence timeline client |
| `/api/v1/intelligence/similarity*` | GET | `intelligence.py` | similarity/memory patterns | API consumers | similarity panel equivalent | limitations present | yes later | intelligence client |
| `/api/v1/intelligence/candles/{candle_id}*` | GET | `intelligence.py` | candle dashboard/event/evidence/similar/attribution DTOs | API consumers | candle detail equivalent | limitations present | yes later | market/candle client |
| `/api/v1/intelligence/narratives*` | GET | `intelligence.py` | narrative memory/heatmap/history | API consumers | narrative panel equivalent | limitations present | yes later | narratives client |
| `/api/v1/signals/latest` | GET | `intelligence_signals.py` | signal list + limitations | API consumers | signals panel equivalent | limitations present | yes later | signals client |
| `/api/v1/signals/news-market-impact` | GET | `intelligence_signals.py` | signal list + limitations | API consumers | impact view equivalent | limitations present | yes later | signals client |
| `/api/v1/signals/{signal_id}` | GET | `intelligence_signals.py` | signal payload + limitations | API consumers | signal detail equivalent | limitations present | yes later | signals client |
| `/api/v1/signals/top` | GET | `signals.py` | ResponseEnvelope paginated signals | API consumers | top signals equivalent | envelope | yes later | signals client; resolve router overlap |
| `/api/v1/evidence/packets*` | GET | `evidence.py` | evidence packet/replay/timeline/relationships | API consumers | evidence panel equivalent | limitations present | yes later | evidence client |
| `/api/v1/observability/snapshot` | GET | `observability.py` | ResponseEnvelope operations snapshot | ops/status | not current Jinja | envelope | maybe | provider-health or ops client |

## 5. Current templates/components inventory

| Template/component path | Route using it | Data required | Interactive behavior | Evidence/candle/timeline/signal/provider behavior |
|---|---|---|---|---|
| `app/web/templates/market/dashboard.html` | `/market` | `market_vm`, `timeframes`, safety limitations | loads `market.js`; chart controls | renders dashboard cards, shock index, provider health, narrative, signals, chart, candle/event/evidence/similarity panels. |
| `app/web/templates/market/time_machine.html` | `/market-time-machine`, `/market/time-machine` | `market_vm`, frame | loads `market.js`; timeline controls | renders chart, candle panel, event panel, evidence panel, similarity, provider health. |
| `app/web/templates/market/section.html` | `/market/{section}` | `market_vm`, `frame`, selected filters/sort | section-specific forms | branches timeline/time-machine/signals/evidence/narratives/sources and always renders provider health. |
| `app/web/templates/market_timeline.html` | `/intelligence/timeline` | `MarketTimelineDTO`, filters/window/sort | filters, pagination | links to `/candles/{id}` and `/evidence/{id}` where available. |
| `app/web/templates/market_time_machine.html` | legacy Time Machine page | `MarketTimelineDTO`, timeframes | date/timeframe form, history buttons | exposes chart, marker panel, candle attribution, evidence side panel, narrative/similarity panels. |
| `app/web/templates/evidence_viewer.html` | `/evidence/{packet_id}` | `EvidencePanelDTO`, `ReplaySummaryDTO` | evidence/replay navigation | shows provider confidence, source confidence, replay refs, limitations. |
| `app/web/templates/candle_attribution.html` | `/candles/{candle_id}` | `CandleAttributionDTO` | links JSON/timeline | shows OHLC, candidate events, attribution confidence, replay availability, limitations. |
| `app/web/templates/components/market_panels.html` | dashboard, section, Time Machine | `market_vm` fields | chart buttons, filter forms | macros for safety flags, timeline controls, provider health, chart, candle/event/evidence/similarity/signals/sources. |
| `app/web/templates/components.html` | legacy timeline/Time Machine/evidence | DTO fields | Alpine/JS/fetch metrics | macros for safety notice, candlestick chart, evidence side panel, empty/error/loading states. |
| `app/web/static/js/market.js` | dashboard/section/time_machine | `data-candle`, `data-marker` JSON | updates selected panels and posts metrics | builds marker details, tracks replay/evidence/candle/zoom/pan interactions. |
| `frontend/components/interactive/BastionCommandPalette.tsx` | Next.js legacy command palette | static nav entries | command links | contains canonical Market route entries only; no dashboard implementation. |

## 6. Market Time Machine contract

- Routes: `/market-time-machine`, `/market/time-machine`, and section route `/market/{section}` when section is `time-machine`; legacy template `market_time_machine.html` also exists.
- Route aliases: `/market-time-machine` should remain as a legacy alias during parity. Section aliases `candles`, `events`, `news`, and `shock-index` normalize to supported sections.
- Data source: `MarketTimeMachineWebService` joins BTC candles, news events/articles, price impact, intelligence signals, narrative snapshots, evidence packets/artifacts, replay logs, and source reputation profiles.
- DTO endpoint: `/web/market-time-machine` is the safest initial Reflex DTO dependency.
- Timeline display: `MarketTimelineDTO.timeline_items`, chart markers, filters, pagination/window controls.
- Candle drilldown: `/candles/{candle_id}` HTML and `/web/candle/{candle_id}` DTO.
- Evidence drilldown: `/evidence/{packet_id}` HTML and `/web/evidence/{packet_id}` DTO.
- Narrative connection: `narrative_panel`, narrative strength, shock index, and `/api/v1/intelligence/narratives*` APIs.
- Signal connection: `signal_summary`, `/market/signals`, `/api/v1/signals/*` APIs.
- Provider/source connection: `provider_health_widget`, `source_summary`, `/market/sources`, `/api/v1/news/sources*` APIs.
- Degraded state: OperationalError handlers return visible fallback payloads with limitations; provider health widget displays degraded source counts.
- Empty state: templates render empty state messages for no events, no attribution, no evidence packets, no similarities, no active narratives.
- Loading/error state: legacy `components.html` has loading/error macros; dashboard templates show unavailable/degraded sections on DB failure.
- Operator-facing limitations: safety flags and `SAFETY_LIMITATIONS` must remain visible.
- Current behavior is display/review oriented. It can post interaction metrics but does not trade, sign, custody, or execute market actions.
- Historical replay exists through evidence replay summaries and replay-open metrics, but Reflex must not claim cryptographic verification unless an endpoint explicitly provides it.
- Confidence/uncertainty are exposed through provider confidence, attribution confidence, source confidence, evidence counts, limitations, and provider-health rows.
- Stale/degraded visibility is required and should be strengthened in Reflex with an explicit Market Degraded Mode Banner.

## 7. Market Intelligence contract

Current behavior includes:

- Latest intelligence and dashboard overview via dashboard cards, narrative panel, shock index, signals panel, and timeline list.
- Signal list via `MarketTimeMachineWebService.signal_summary` and `signals_view` macro.
- News-market impact data through news events, price impact, chart markers, `/api/v1/signals/news-market-impact`, and `/api/v1/intelligence/timeline/news-impacts/*`.
- Confidence scoring through marker confidence, provider confidence, attribution confidence, signal confidence, source confidence, and evidence counts.
- Evidence connection through `evidence_url`, evidence panels, replay URLs, and evidence packet DTOs.
- Delivery logs are exposed by `/api/v1/signals/{signal_id}/delivery-logs`, not by current Jinja dashboard.
- Source attribution through `source_summary`, source confidence, provider health, and source registry APIs.
- Provider health visibility through the `provider_health_widget` and source/provider confidence data.
- Limitations copy is sourced from `SAFETY_LIMITATIONS`, signal limitations, evidence limitations, and market-memory safety docs.
- Required final copy: Advisory-only. Not financial advice. Not trading instruction. Signals may be incomplete, stale, wrong, or provider-limited. Operator review is required before acting. No custody. No transaction signing. No automatic trading.

## 8. Evidence integration contract

- Evidence links are generated in templates from DTO fields such as `event.evidence_url`, `/evidence/{packet_id}`, `/web/evidence/{packet_id}`, `/api/v1/evidence/packets/{packet_id}`, and candle evidence APIs.
- Evidence packet IDs are integers in web routes and DTOs; some event links use timeline/event IDs as evidence entry points.
- Evidence details are rendered by `/evidence/{packet_id}` and `evidence_viewer.html`; DTO detail is `/web/evidence/{packet_id}`; API detail is `/api/v1/evidence/packets/{packet_id}`.
- Evidence replay exists through `EvidenceReplayService`, `/api/v1/evidence/replay/{entity_type}/{entity_id}`, replay summaries, and replay links.
- Evidence chain/proof packet concepts are visible through evidence panel limitations, integrity status, replay availability, artifact counts, source confidence, and export URLs.
- Missing evidence is handled through DTO fallback limitations such as evidence unavailable or packet not generated.

Reflex must preserve evidence links, packet drilldown, missing evidence states, provider disagreement/source confidence visibility, and auditability.

## 9. Signal integration contract

- Top signals: `/api/v1/signals/top` from `signals.py` returns `ResponseEnvelope[PaginatedData[SignalOut]]`.
- Latest signals: `/api/v1/signals/latest` from `intelligence_signals.py` returns data + limitations.
- Signal explanation/recommendations: `/api/v1/signals/{signal_id}/explanation` and `/api/v1/signals/{signal_id}/recommendations` from `signals.py`.
- News-market impact signals: `/api/v1/signals/news-market-impact` from `intelligence_signals.py`.
- Evidence links: `/api/v1/signals/{signal_id}/evidence` and market DTO signal items.
- Delivery logs: `/api/v1/signals/{signal_id}/delivery-logs`.
- Suppression/operator-review state: signal governance exposes status, policy decision, `requires_operator_review`, and delivery/publication related fields.
- Potential conflict: both `signals.py` and `intelligence_signals.py` mount at `/api/v1/signals`. Reflex client must test endpoint resolution and avoid assuming one router owns all signal paths.
- Recommended Reflex client path: `services/signals_client.py` should wrap both ResponseEnvelope and plain data+limitations shapes.

## 10. Provider health / degraded mode contract

Current provider/degraded sources:

- `provider_health_widget` in `components/market_panels.html`.
- `_empty_provider_health()` in `app/web/view_models/market.py`.
- source reputation profiles in `MarketTimeMachineWebService.source_summary`.
- `/api/v1/market/providers/health` and `/api/v1/market/btc/providers/health`.
- `/api/v1/market/health`.
- `/api/v1/news/sources/health` and per-source health/snapshot endpoints.
- `/api/v1/observability/snapshot` for broader operations health.

Future Reflex UI must show:

- Degraded Mode Banner.
- stale data warning.
- provider trust/source matrix.
- confidence limitations.
- source disagreement / provider-unavailable rows.
- pipeline lag when exposed by DTOs or observability.
- provider recovered state when exposed by backend data.

## 11. Safety and no-financial-advice copy contract

Required copy for future Reflex Market surfaces:

- Advisory-only.
- Not financial advice.
- Not trading instruction.
- Signals may be incomplete, stale, wrong, or provider-limited.
- Operator review is required before acting.
- No custody.
- No transaction signing.
- No automatic trading.

Forbidden user-facing claim categories to avoid:

- guaranteed-profit language.
- guaranteed-signal language.
- approved-trade language.
- risk/free certainty language.
- sure-win language.
- buy-now or sell-now instruction language.
- any sentence that presents Market Intelligence itself as financial advice.

Search result: current market-related app/web and API code did not show affirmative forbidden market claims. The search found only negated safety statements such as “not financial advice” and safety tests containing forbidden examples.

## 12. No-custody / no-execution audit

Audit result: current Market/Time Machine surfaces are display/review/metrics surfaces. They do not request seed phrases, private keys, wallet files, or signing material. They do not trigger trading, transaction signing, treasury transfers, or automatic profit actions.

Current inputs:

| Route/template | Input | Expected value | Risk level | Validation/current handling | Future Reflex validation |
|---|---|---|---:|---|---|
| `/market`, `market_panels.timeline_controls` | `date` | date string | low | passed as query; selected date stored in view model | validate date format; do not execute actions. |
| `/market`, `/market/time-machine` | `timeframe` | one of `1m`, `5m`, `15m`, `1h`, `4h`, `1d` | low | route defaults to `1h` if unsupported | enforce enum. |
| `/market/{section}` | `status` | signal status filter | low | view filter only | enum/allowlist. |
| `/market/{section}` | `sort` | source sort | low | source summary sorting | enum/allowlist. |
| `/intelligence/timeline` | `filter`, `page`, `page_size`, `sort`, `window` | timeline filters/window/page | low | FastAPI Query bounds for page/page_size, service filter normalization | enum/allowlist and numeric bounds. |
| `/web/*/marker-click`, candle/replay/evidence metrics | metric fields | marker/timeframe only | low | bounded metric labels | keep telemetry-only; no domain action. |

## 13. Future Reflex route ownership decision

| Current route | Decision | Rationale |
|---|---|---|
| `/market` | Reflex owns primary route after parity | Public/console dashboard should be Reflex once full DTO and safety parity exists. |
| `/market-time-machine` | deprecated alias after parity | Keep as redirect/alias to `/market/time-machine` during and after cutover window. |
| `/market/time-machine` | Reflex mirrors first, owns later | Highest-risk Time Machine route; requires chart/candle/evidence parity. |
| `/market/timeline` | Reflex owns later | Can use `/web/timeline` initially. |
| `/market/signals` | Reflex owns later | Requires signal router conflict resolution and no-advice copy. |
| `/market/evidence` | Reflex owns later | Must preserve Evidence/Proof Packet UI work. |
| `/market/narratives` | Reflex owns later or P2 | Narrative APIs exist but UI parity can follow core Time Machine. |
| `/market/sources` | Reflex owns later or P2 | Needs provider/source matrix parity. |
| `/market/{section}` legacy aliases | deprecated aliases | Keep only with explicit redirect/alias plan. |
| `/intelligence/timeline` | keep alias / API-backed route | Useful existing public URL; Reflex may route or redirect. |
| `/evidence/{packet_id}` | keep alias during evidence parity | Must not break existing packet links. |
| `/candles/{candle_id}` | keep alias during candle parity | Must not break drilldowns. |
| `/web/*` DTO endpoints | backend/API-only | Reflex should call these; do not render pages from them. |

## 14. Proposed Reflex market routes

| Route | Purpose | Required data | Required components | Required API client method | Required safety copy | States | Priority |
|---|---|---|---|---|---|---|---|
| `/market` | Market Intelligence overview | `/web/market-time-machine`, provider health, signal summary | market_dashboard, market_header, market_status_banner, provider_health_panel | `market_client.get_dashboard()` | no advice/no trading/no custody | loading/error/empty/degraded/stale | P0 |
| `/market/timeline` | timeline list/filter view | `/web/timeline`, `/api/v1/intelligence/timeline*` | market_timeline, market_timeline_chart | `market_time_machine_client.get_timeline()` | no advice/correlation | loading/error/empty/degraded/stale | P1 |
| `/market/time-machine` | chart + candle/evidence replay | `/web/market-time-machine`, `/web/candle/{id}`, `/web/evidence/{id}` | market_time_machine, candle_card/detail, evidence_panel | `market_time_machine_client.get_dashboard()` | no advice/correlation/operator review | loading/error/empty/degraded/stale | P0 |
| `/market/signals` | signal list/detail | `/api/v1/signals/*` | market_signal_list, market_signal_card | `signals_client.get_latest()`, `get_top()` | not trading instruction | loading/error/empty/degraded | P1 |
| `/market/evidence` | evidence overview | `/web/evidence/{id}`, `/api/v1/evidence/*` | market_evidence_panel | `evidence_client.get_market_evidence()` | evidence limitations | loading/error/empty/degraded | P1 |
| `/market/narratives` | narrative memory | `/api/v1/intelligence/narratives*` | market_narrative_panel | `intelligence_client.get_narratives()` | historical context only | loading/error/empty/stale | P2 |
| `/market/sources` | sources/providers | `/api/v1/news/sources*`, provider health | market_source_panel, provider_trust_matrix | `provider_health_client.get_sources()` | source limitations | loading/error/empty/degraded | P2 |
| `/console/market-intelligence` | operator console module | overview + provider/source health | console market module | console/market clients | operator review required | loading/error/degraded | P1 |
| `/console/time-machine` | operator Time Machine module | Time Machine DTOs | console time-machine module | time-machine client | no execution | loading/error/degraded | P1 |

## 15. Proposed Reflex market components

Required target components:

```text
components/market/
  market_dashboard.py
  market_header.py
  market_status_banner.py
  market_time_machine.py
  market_timeline.py
  market_candle_card.py
  market_candle_detail.py
  market_signal_card.py
  market_signal_list.py
  market_narrative_panel.py
  market_source_panel.py
  market_evidence_panel.py
  market_provider_health_panel.py
  market_degraded_banner.py
  market_limitations_card.py

components/console/
  market_intelligence_module.py
  time_machine_module.py

components/charts/
  market_timeline_chart.py
  signal_confidence_chart.py
  provider_trust_matrix.py
  risk_heatmap.py
```

## 16. Proposed Reflex market services

| Client | Method | Backend endpoint | Expected response | Error/timeout/empty/degraded behavior |
|---|---|---|---|---|
| `market_client.py` | `get_dashboard()` | `/web/market-time-machine` | merged Time Machine DTO + VM | unwrap/return JSON; show Market degraded banner on empty/timeout. |
| `market_client.py` | `get_health()` | `/api/v1/market/health` | health dict | visible provider/source status. |
| `market_time_machine_client.py` | `get_timeline(filter,page,window)` | `/web/timeline` | `MarketTimelineDTO` | empty timeline state + limitations. |
| `market_time_machine_client.py` | `get_candle(candle_id)` | `/web/candle/{candle_id}` | `CandleAttributionDTO` | no attribution state + limitations. |
| `market_time_machine_client.py` | `get_evidence(packet_id)` | `/web/evidence/{packet_id}` | `EvidencePanelDTO` | evidence unavailable state. |
| `intelligence_client.py` | `get_narratives()` | `/api/v1/intelligence/narratives` | narrative data | historical-context-only limitations. |
| `intelligence_client.py` | `get_sources()` | `/api/v1/news/sources` | source registry | source empty/degraded matrix. |
| `signals_client.py` | `get_latest()` | `/api/v1/signals/latest` | data + limitations | no trading instruction state. |
| `signals_client.py` | `get_top()` | `/api/v1/signals/top` | ResponseEnvelope paginated data | unwrap envelope. |
| `evidence_client.py` | `get_packet(packet_id)` | `/api/v1/evidence/packets/{packet_id}` | data + limitations | packet unavailable state. |
| `provider_health_client.py` | `get_market_providers()` | `/api/v1/market/providers/health` or `/api/v1/market/btc/providers/health` | provider health dict | stale/degraded provider matrix. |

## 17. Proposed Reflex market state modules

```text
state/
  market_state.py
  market_time_machine_state.py
  market_signal_state.py
  market_evidence_state.py
  provider_health_state.py
```

Each state module must include: loading, error, empty, stale, degraded, selected candle, selected signal, selected evidence packet, active section, filters, and selected timeframe/window where supported.

## 18. Migration risks

| Risk | Category | Mitigation |
|---|---|---|
| Breaking current `/market` operator dashboard | BLOCKER | Keep FastAPI/Jinja canonical until Reflex route parity tests pass. |
| Breaking candle drilldown | BLOCKER | Preserve `/candles/{candle_id}` alias and `/web/candle/{candle_id}` DTO. |
| Breaking evidence links | BLOCKER | Preserve `/evidence/{packet_id}`, `/web/evidence/{packet_id}`, and API evidence packet routes. |
| Hiding degraded/stale states | BLOCKER | Reflex must include Market degraded/stale banners and provider matrix. |
| Turning advisory signals into trading advice | BLOCKER | Mandatory no-advice/no-trading copy and tests. |
| Duplicate route ownership | HIGH | Use explicit parity phase routing plan; do not replace backend route until cutover prompt. |
| Diverging DTO schema between Jinja and Reflex | HIGH | Create typed Reflex client around `/web/*` DTOs before UI migration. |
| Signal router overlap under `/api/v1/signals` | HIGH | Write client tests for both `signals.py` and `intelligence_signals.py` shapes. |
| Provider health source mismatch | HIGH | Decide provider-health canonical endpoint before Prompt 12. |
| Regressing tests | MEDIUM | Keep market-specific tests green and add Reflex route tests. |
| Calling non-existing backend endpoints | HIGH | Initial Reflex clients should call current `/web/*` DTOs first. |

## 19. Blockers before Prompt 11/22

- BLOCKER: Define typed Reflex client models for `/web/market-time-machine`, `/web/timeline`, `/web/candle/{candle_id}`, and `/web/evidence/{packet_id}`.
- BLOCKER: Preserve FastAPI/Jinja `/market` and `/market/time-machine` as canonical until Reflex parity tests pass.
- BLOCKER: Preserve evidence and candle drilldown aliases during parity.
- BLOCKER: Add no-advice/no-trading/no-custody copy tests for Reflex Market pages.
- HIGH: Resolve `/api/v1/signals` router shape overlap in Reflex client tests.
- HIGH: Pick provider-health canonical endpoint or adapter strategy.
- HIGH: Define chart/candle/marker event model for Reflex without relying on stringified DOM JSON.
- MEDIUM: Document legacy alias redirect rules for `/market-time-machine` and `/market/{section}` aliases.
- MEDIUM: Add DTO schema snapshots for Market Time Machine.
- LOW: Add visual polish and chart animation parity after functional parity.

## 20. Acceptance criteria for future Market migration

Future Prompt 11/22 and 12/22 work is acceptable only when:

- Reflex Market routes are implemented without deleting FastAPI/Jinja routes.
- `/web/*` DTO clients unwrap and display limitations/degraded states.
- `/market` and `/market/time-machine` parity route tests pass.
- Candle drilldown and evidence packet links remain available.
- Provider health/source matrix remains visible.
- Signal pages include no-advice/no-trading/operator-review copy.
- Reflex does not introduce trading, custody, signing, or treasury transfer UI.
- Degraded/stale/fallback states are tested and visible.
- FastAPI/Jinja remains available for rollback until cutover.

## Verification results recorded during Prompt 10

| Command | Result |
|---|---|
| `python -m pytest -q tests -k "market or intelligence or time_machine or evidence"` | Passed: 125 passed, 700 deselected, 71 warnings. |
| `python -m pytest -q` | Failed due known baseline blockers outside this contract: 14 failed, 868 passed, 2 skipped, 99 warnings. |
| `cd frontend && npm run typecheck && npm run test && npm run build` | Passed; warnings included npm `http-proxy` warning, Vite CJS deprecation, and Next.js telemetry notice. |

No Market migration, route replacement, backend domain-logic change, or production cutover occurred.
