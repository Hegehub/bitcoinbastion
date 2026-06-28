# Reflex Market Intelligence Dashboard

Date: 2026-06-22  
Status: partial implementation for Prompt 11/22. FastAPI/Jinja remains canonical for `/market` and Market Time Machine routes.

## 1. Purpose

Prompt 11/22 adds a parallel Reflex operator overview at `/console/market-intelligence`. The page summarizes Market Intelligence status, latest signal availability, provider health, evidence availability, freshness, degraded states, and the intentionally deferred Time Machine migration.

This prompt does not replace `/market`, `/market/time-machine`, `/market/timeline`, `/market/signals`, `/market/evidence`, `/market/narratives`, `/market/sources`, `/console/time-machine`, or any FastAPI/Jinja dashboard route.

## 2. Route

| Route | Status | Owner in this prompt | Notes |
|---|---|---|---|
| `/console/market-intelligence` | implemented | Reflex | Operator overview route registered in `bastion_ui/app.py`. |
| `/market` | unchanged | FastAPI/Jinja | Public Market dashboard is not migrated in this prompt. |
| `/market/time-machine` | unchanged | FastAPI/Jinja | Full Time Machine remains deferred to Prompt 12/22. |

## 3. Backend endpoints used

The Reflex service client uses only existing backend endpoints documented in the Prompt 10 contract:

| Client method | Endpoint | Purpose | Fallback behavior |
|---|---|---|---|
| `get_market_dashboard()` | `/web/market-time-machine` | Existing Market DTO overview. | Returns unavailable/degraded `ApiResult` on API error. |
| `get_market_status()` | `/api/v1/market/health` | Market health summary. | Returns unavailable/degraded `ApiResult` on API error. |
| `get_market_regime()` | `/web/market-time-machine` | Reuses dashboard DTO until a dedicated regime endpoint exists. | Returns explicit unavailable reason. |
| `get_latest_intelligence_signals()` | `/api/v1/signals/latest` | Latest intelligence signals. | Returns unavailable/degraded `ApiResult` on API error. |
| `get_provider_health()` | `/api/v1/market/providers/health` | Provider health overview. | Returns unavailable/degraded `ApiResult` on API error. |
| `get_evidence_summary()` | `/api/v1/evidence/packets` | Evidence packet availability. | Returns explicit not-connected reason if unavailable. |

## 4. Missing backend endpoints

- Dedicated Market regime endpoint: missing; the Reflex client reuses `/web/market-time-machine` conservatively.
- Dedicated dashboard evidence summary endpoint: missing; the client calls `/api/v1/evidence/packets` and shows unavailable state on failure.
- Canonical provider-health endpoint still needs adapter confirmation because Prompt 10 found overlapping Market health routes.
- Full Time Machine timeline/candle/replay/narrative/similarity endpoints remain deferred to Prompt 12/22.

## 5. Components added

- `components/market/market_intelligence_dashboard.py`
- `components/market/market_status_banner.py`
- `components/market/market_regime_card.py`
- `components/market/latest_signals_panel.py`
- `components/market/provider_health_strip.py`
- `components/market/evidence_summary_panel.py`
- `components/market/data_freshness_panel.py`
- `components/market/time_machine_teaser.py`

## 6. State model

`MarketState` exposes loading, error, market status, market regime, latest signals, provider health, evidence summary, freshness, degraded reasons, and last-updated labels. State methods load each panel independently and preserve visible unavailable/degraded state rather than inventing data.

## 7. Safety copy

Visible dashboard copy includes:

- Market intelligence is advisory-only.
- Not financial advice.
- Not a trading recommendation.
- Signals may be incomplete, stale, degraded, or wrong.
- Always verify using independent sources.
- Bitcoin Bastion does not custody funds and does not execute trades.

The dashboard also states that no seed phrase input, private key input, wallet file upload, trading API key input, exchange secret input, or automatic trade execution is supported.

## 8. Degraded/stale handling

The dashboard surfaces unavailable backend data as degraded state. Provider health, evidence summary, signal availability, and freshness panels have safe default labels until backend data is loaded. API errors return `ApiResult(ok=False, degraded=True)` instead of fake success.

## 9. Deferred to Prompt 12/22

- Full Market Time Machine.
- Candle timeline and candle detail migration.
- Signal replay and historical signal detail.
- Evidence drilldown inside Market-specific routes.
- Narratives, sources, and historical similarity views.
- `/console/time-machine`.

## 10. Verification commands

Recorded for this prompt:

| Command | Result |
|---|---|
| `cd reflex_frontend && uv sync` | Passed: dependencies resolved/audited. |
| `python -m pytest -q reflex_frontend/bastion_ui/tests/test_market_intelligence_route.py reflex_frontend/bastion_ui/tests/test_market_safety_copy.py reflex_frontend/bastion_ui/tests/test_market_client.py reflex_frontend/bastion_ui/tests/test_market_no_trading_claims.py` | Passed: 9 passed. |
| `python -m pytest -q` | Failed with known repository baseline blockers: async pytest plugin gaps for MCP/SDK tests and a pre-existing Reflex contract expectation; 14 failed, 868 passed, 2 skipped, 99 warnings. |
| `cd reflex_frontend && uv run ruff check .` | Passed. |
| `cd reflex_frontend && uv run mypy bastion_ui` | Passed: no issues in 186 source files. |
| `cd reflex_frontend && uv run pytest` | Passed: 64 passed. |
| `cd reflex_frontend && uv run reflex export` | Passed with warnings for default sitemap plugin, deprecated `App(theme=...)`, and Node.js version below Reflex recommendation. |
