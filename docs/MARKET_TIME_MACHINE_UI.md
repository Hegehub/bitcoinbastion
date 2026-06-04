# Market Time Machine UI

The Market Time Machine dashboard is the production web interface for Bitcoin Bastion market memory. It preserves the existing Bitcoin-first visual language: simple cards, clear typography, high contrast, operator control, and evidence-first explanations.

## Architecture

Task 41 finalizes the dashboard as a **FastAPI + Jinja2 + HTMX + Alpine.js** web surface. The web layer is intentionally thin:

- templates render DTOs supplied by backend services;
- no frontend price, attribution, confidence, or similarity calculations are performed;
- routes never expose stack traces and show empty/error/degraded states instead;
- the existing Trace UI and public frontend remain untouched.

The previously added React `/market` prototype has been removed from the production dashboard path because this surface must stay compatible with the non-SPA web architecture.

## Routes

Production web pages:

- `GET /market-time-machine` — primary dashboard with time controls, BTC chart, markers, timeline panel, attribution panel, and evidence entry point.
- `GET /intelligence/timeline` — unified timeline with filtering, sorting, pagination, and time-window controls.
- `GET /evidence/{packet_id}` — evidence packet viewer with confidence, provider/source health, replay references, limitations, and integrity status.
- `GET /candles/{candle_id}` — candle attribution view with OHLC, price change, candidate events/articles, confidence, replay availability, and limitations.

Thin DTO endpoints for HTMX/Alpine or self-hosted integrations:

- `GET /web/market-time-machine`
- `GET /web/timeline`
- `GET /web/candle/{id}`
- `GET /web/evidence/{id}`

## Components and Templates

Reusable Jinja components live in `app/web/templates/components.html`:

- `btc_candlestick_chart`
- evidence side panel
- status badges
- safety notice
- loading skeleton
- empty state
- error state

The candlestick component supports timeframe switching, zoom controls, pan controls, responsive horizontal overflow, keyboard focus, and deterministic marker rendering.

## Marker System

Markers are deterministic backend DTOs, not frontend inference. Supported marker classes are:

- positive
- negative
- uncertain
- security
- regulatory
- institutional / ETF
- mining
- Lightning / Bitcoin Core

Duplicate markers are suppressed by timestamp bucket and marker type so repeated events do not visually stack on the same candle.

## Attribution Flow

Clicking a candle opens `/candles/{candle_id}`. The page displays:

- OHLC and volume;
- price change percentage;
- candidate events;
- candidate articles;
- confidence;
- time distance;
- historical similarity count;
- replay availability;
- limitations.

Every attribution surface repeats: **Correlation is not proof of causation.**

## Evidence Panel and Replay Integration

Evidence views expose:

- evidence packet ID;
- replay availability;
- evidence sources;
- provider confidence;
- source confidence;
- integrity status;
- operator review status;
- limitations.

Replay open events are observable through bounded metrics, and replay-unavailable states remain visible.

## Mobile and Accessibility

- Mobile layouts stack panels and preserve chart usability through horizontal overflow.
- Controls are touch-friendly and keyboard-focusable.
- Chart and navigation regions include ARIA labels.
- IDs and hashes use monospace formatting.
- Native `<details>` elements provide accessible expandable evidence sections.

## Safety Copy

Every Market Time Machine page displays:

```text
Correlation is not proof of causation.
Bitcoin Bastion provides evidence-based informational analysis.
Nothing displayed here constitutes financial advice.
```

## Known Limitations

- The dashboard depends on populated backend market-memory tables.
- Missing evidence packets render as explicit empty states.
- Provider degradation and backend timeouts render safe error messages without internal exceptions.
- Chart rendering is intentionally minimal and self-hosted friendly; future prompts may add richer canvas/SVG interactions without moving business logic into the browser.
