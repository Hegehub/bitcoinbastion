# Reflex Market Time Machine

Date: 2026-06-23  
Status: partial Reflex parity layer for Prompt 12/22. Existing FastAPI/Jinja Market routes remain active.

## 1. Purpose

Prompt 12/22 adds Reflex pages for Market Time Machine, timeline, signals, evidence, narratives, and sources. These pages are frontend parity surfaces that render safely without backend data and call only documented read-only backend DTO/API endpoints through the Reflex Market client.

No FastAPI/Jinja dashboard, Next.js surface, backend market service, trading execution, custody flow, or wallet/signing behavior was removed or replaced.

## 2. Routes implemented

| Reflex route | Status | Purpose |
|---|---|---|
| `/market` | implemented | Reflex index page linking Market sections; not production cutover. |
| `/market/time-machine` | implemented | Evidence-driven BTC market reconstruction overview. |
| `/market/timeline` | implemented | Timeline events, evidence links, and provider state placeholders. |
| `/market/signals` | implemented | Advisory market observations with review/limitations framing. |
| `/market/evidence` | implemented | Market evidence packets as audit/supporting context. |
| `/market/narratives` | implemented | Evidence-based reconstructions with uncertainty visible. |
| `/market/sources` | implemented | Provider/source health, freshness, and degraded-state visibility. |

## 3. Backend endpoint mapping

| Reflex route/client method | Backend endpoint | Data shape | Status | Known limitations |
|---|---|---|---|---|
| `/market/time-machine`, `get_time_machine()` | `/web/market-time-machine` | Market Time Machine DTO / merged dashboard JSON | implemented client mapping | Complex chart parity remains basic structured cards. |
| `/market/timeline`, `get_timeline()` | `/web/timeline` | Timeline DTO JSON | implemented client mapping | Pagination/filter UI is minimal. |
| `get_candle_detail(candle_id)` | `/web/candle/{candle_id}` | Candle attribution DTO JSON | implemented client mapping | Detail route is not migrated in this prompt. |
| `get_evidence_packet(packet_id)` | `/web/evidence/{packet_id}` | Evidence panel DTO JSON | implemented client mapping | Detailed packet route remains shared Evidence/Trace work. |
| `/market/signals`, `get_market_signals()` | `/api/v1/signals/latest` | signal list payload | implemented client mapping | Signal router shapes overlap; client handles fallback. |
| `/market/evidence`, `get_market_evidence()` | `/api/v1/evidence/packets` | evidence packet payload | implemented client mapping | Dedicated Market evidence summary endpoint is not finalized. |
| `/market/narratives`, `get_market_narratives()` | `/api/v1/intelligence/narratives` | narrative payload | implemented client mapping | Narrative schema may differ from Jinja view model. |
| `/market/sources`, `get_market_sources()` | `/api/v1/news/sources` | source registry payload | implemented client mapping | Provider health canonical adapter still needs final decision. |

## 4. Data normalization rules

Market state normalizes backend payloads into UI-safe dictionaries and lists for timeline events, signals, evidence packets, narratives, sources, selected candle id, selected evidence packet id, selected asset, selected range, stale/degraded state, and last-updated labels.

Missing optional fields become visible unavailable states. Empty arrays remain empty; the UI does not fabricate records.

## 5. Safety copy

Market pages visibly state:

- Not financial advice.
- Not a trading instruction.
- Not a price guarantee.
- Historical similarity is advisory-only.
- Signals require operator review.
- Provider disagreement and stale data reduce confidence.

No market page requests seed phrases, private keys, wallet files, exchange API secrets, or signing material. No market page executes trades, signs transactions, or approves treasury actions.

## 6. Degraded/stale data behavior

Every Market route renders a degraded/stale banner by default. The Market client returns `ApiResult(ok=False, degraded=True)` for HTTP errors, timeouts, missing endpoints, or unavailable backend data. Provider disagreement and stale provider state are surfaced as confidence limitations.

## 7. Current limitations

- Complex charting is intentionally not implemented in this prompt.
- Candle detail and evidence packet detail routes are linked conceptually but not deeply migrated here.
- Narratives and sources use conservative cards until exact DTO parity is proven.
- The existing FastAPI/Jinja dashboard remains canonical during parity.

## 8. Remaining parity gaps

- Full chart/marker interaction parity.
- Timeline filter and pagination parity.
- Candle drilldown route parity.
- Market-specific evidence packet drilldown parity.
- Narrative memory and historical similarity parity.
- Source/provider trust matrix parity.
- Final route ownership/cutover decision.

## 9. Manual verification steps

1. Start the Reflex app in the `frontend` environment.
2. Visit `/market`, `/market/time-machine`, `/market/timeline`, `/market/signals`, `/market/evidence`, `/market/narratives`, and `/market/sources`.
3. Confirm each route renders safety copy, degraded/unavailable state, section navigation, and limitations.
4. Confirm FastAPI/Jinja `/market` and `/market/time-machine` remain intact outside Reflex cutover.

## 10. Verification commands

| Command | Result |
|---|---|
| `python -m pytest -q tests/security/test_developer_layer_forbidden_wording.py frontend/bastion_ui/tests/test_market_safety.py frontend/bastion_ui/tests/test_market_no_trading_claims.py` | Passed: 7 passed. |
| `cd frontend && uv run ruff check .` | Passed. |
| `cd frontend && uv run mypy bastion_ui` | Passed: no issues in 215 source files. |
| `cd frontend && uv run pytest` | Passed: 75 passed. |
| `cd frontend && uv run reflex export` | Passed with warnings for default sitemap plugin config, deprecated `App(theme=...)`, and Node.js below the recommended version. |
| `python -m pytest -q` | Failed with known baseline blockers: async pytest plugin gaps for MCP/SDK tests and a pre-existing Reflex contract expectation; 14 failed, 868 passed, 2 skipped, 99 warnings. |
