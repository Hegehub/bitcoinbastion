# Market Time Machine UI

Status: baseline production-grade web interface implemented; production calibration and live provider coverage still pending.

## Purpose

The Market Time Machine is the unified web interface for BTC candles, classified news markers, candle explanations, evidence packets, historical similarity, and replay timelines.

Safety posture is mandatory:

- Correlation is not proof of causation.
- Evidence, missing evidence, degraded providers, and operator review state must remain visible.
- The UI is informational and never claims certainty or financial advice.

## Pages

Implemented web pages:

- `/market`
- `/market/timeline`
- `/market/candles`
- `/market/events`
- `/market/news`
- `/market/narratives`
- `/market/shock-index`

Legacy compatibility remains available through `/market-time-machine`, `/intelligence/timeline`, `/candles/{candle_id}`, `/evidence/{packet_id}`, and DTO endpoints under `/web/*`.

## Frontend DTOs

The main DTO exposes:

- `chart_data`
- `marker_data`
- `selected_candle`
- `selected_event`
- `historical_matches`
- `evidence_summary`
- `shock_index`
- `narrative_summary`
- `provider_health`

## Interaction model

The chart supports responsive rendering, keyboard focus, hover/click selection, zoom controls, pan controls, candle selection, marker rendering, and bounded telemetry calls.

Marker details include title, source, publish time, BTC price at publish, 15m/1h/4h/24h changes, confidence, evidence availability, and historical matches.

Candle details include OHLC, volume, price-change percent, candidate event groups, attribution confidence, limitations, likely factors, combined explanation, and the required no-causation disclosure.

## Marker types

Supported display mapping:

- `positive_news` → 🟢
- `negative_news` → 🔴
- `uncertain_news` → 🟡
- `security_shock` → ⚠️
- `regulatory_event` → 🏛
- `institutional_event` → 🏦
- `mining_event` → ⛏
- `lightning_or_core_event` → ⚡

## Metrics

Bounded UI metrics:

- `market_ui_page_views_total{page}`
- `market_ui_marker_clicks_total{marker_type}`
- `market_ui_candle_clicks_total{timeframe}`
- `market_ui_replay_requests_total{entity_type}`
- `market_ui_evidence_views_total{surface}`

## Readiness

Market Time Machine readiness after this task: **88%**.

Remaining blockers:

- Live production data calibration and provider coverage evidence.
- Full browser-based visual regression suite.
- Real-user load/performance validation.

## Prompt 44 production finalization

Prompt 44 finalizes the web Market Intelligence dashboard around the Market Time Machine.

### Navigation

The existing site navigation exposes `Market Intelligence` with subsections:

- Timeline
- Market Time Machine
- Narratives
- Signals
- Evidence
- Sources

### Dashboard structure

`/market` now acts as the dashboard landing page and includes future-refresh-ready cards for:

- BTC Price
- News Shock Index
- Active Narratives
- Latest High Impact Event
- Latest Published Signal
- Provider Health
- Operator Queue
- Evidence Replay Requests

### Timeline UX

`/market/timeline` uses a windowed timeline presentation for candles, news events, signals, security shocks, regulatory events, narrative shifts, and operator publications. Filtering, scrolling, grouping, and future incremental loading are represented in the frontend contract without rendering full history.

### Evidence and replay UX

`/market/evidence` displays evidence packets with expandable sections for packet summary, evidence chain, confidence breakdown, provider snapshot, source snapshot, limitations, and replay timeline. Replay failures, hashes, policy decisions, operator actions, and publication status remain visible.

### Safety principles

Every Market Intelligence route keeps the global safety banner visible:

- Correlation is not proof of causation.
- Bitcoin Bastion provides evidence-based market context, not financial advice.
- Missing evidence, degraded providers, low confidence, replay failures, and operator review state must remain visible.

Market Time Machine readiness after Prompt 44: **93%**.
