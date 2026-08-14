# Prompt 9R3 — Jobs, Market Overview, and Market Signals

## Initial remaining-gap table

| Gap ID | Domain | Operation/family | DTO | Adapter | State | Trigger | Render | Degraded | A11y | Browser | Required fix |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P9R3-G01 | Jobs | `jobs_api_v1_operations_jobs_get` | `BackgroundJobHealthOut` | absent | absent | absent | placeholder | absent | absent | absent | typed projection, protected route lifecycle, dense list |
| P9R3-G02 | Market Overview | raw duplicate BTC price routes | unconstrained dictionary | raw-dict client | raw-dict State | legacy refresh | index placeholder | global-only | incomplete | absent | typed bounded `/market/overview`, projection, State, named DOM |
| P9R3-G03 | Market Signals | `top_signals_api_v1_signals_top_get` | `SignalOut` | absent | raw-dict legacy State | absent | static placeholder | absent | incomplete | absent | typed projection, route lifecycle, semantic list |

## Final ownership and coverage

| Domain | Canonical operation | Generated DTO | Adapter / view model | State / trigger | Named DOM fields | Feature-52 | Coverage |
|---|---|---|---|---|---|---|---|
| Jobs | `jobs_api_v1_operations_jobs_get` | `BackgroundJobHealthOut` | `adapt_jobs` / `JobViewModel` | `JobsState.load` on `operations.jobs` | `.job-name`, `.job-status`, timing, next run, bounded failure | LIVE per successful read | IMPLEMENTED_UNVERIFIED (protected runtime denial verified) |
| Market Overview | `market_current_overview` | `BTCMarketOverviewEnvelope` | `adapt_market_overview` / `MarketOverviewViewModel` | `MarketOverviewState.load` on `market.home` | `market-price`, `market-pair`, `market-observed`, `market-confidence`, `market-source` | LIVE per successful read | IMPLEMENTED_VERIFIED |
| Market Signals | `top_signals_api_v1_signals_top_get` | `SignalOut` | `adapt_market_signals` / `MarketSignalViewModel` | `MarketSignalsState.load` on `market.signals` | signal type, severity, confidence, backend score, publication status, time | LIVE per successful read | IMPLEMENTED_VERIFIED empty state; row rendering unit-verified |

## Market semantic ownership

| UI concept | Backend field | Backend-owned meaning | Allowed frontend transformation |
|---|---|---|---|
| Reference price | `BTCMarketOverviewOut.price_usd` | persisted current provider observation | Decimal-preserving USD label |
| Provider confidence | `provider_confidence` | backend/provider confidence | Decimal display only |
| Source | `source` | persisted observation provider or store | text only |
| Observation time | `observed_at` | backend capture time | text formatting only |
| Limitations | `limitations[]` | backend absence/availability limitation | list rendering only |
| Market regime/direction | absent | no backend meaning in this contract | omitted |

`frontend_market_conclusion_recomputations = 0`.

## Signal semantic ownership

| UI field | Backend field | Backend authority | Frontend formatting only? |
|---|---|---|---|
| Type | `signal_type` | backend taxonomy | yes |
| Severity | `severity` | backend classification | yes |
| Confidence | `confidence` | backend Decimal | yes; no normalization/averaging |
| Backend score | `score` | backend analytical score | yes; never mapped to direction/strength |
| Publication status | `is_published` | backend publication fact | boolean text label |
| Observed time | `created_at` | backend creation time | text formatting |
| Freshness | `freshness.is_stale/stale_reason` | backend freshness evaluation | conditional text |
| Direction/strength/expiry | absent | unavailable | omitted |

`frontend_signal_semantic_derivations = 0`. Empty signals render an authoritative empty result, never “neutral market.” No execution, position, leverage, wallet, or custody controls exist.

## Feature-59/60 and degradation

The canonical lifecycle renders typed unavailable/error states without fixtures. Deterministic Feature-60 objects use fixed `2026-01-15T12:00:00Z`, fixed content, and `DEMO_FIXTURE`; they are imported only by tests and never by production State. Scenarios cover empty Jobs, unavailable Market, and empty Signals. Backend-safe failure projection excludes worker identity, traceback, environment, command arguments, credentials, and raw DTOs.

## Browser evidence (2026-08-11 UTC)

Chromium 151 was installed through Playwright 1.58 in the disposable frontend environment. Real Reflex ran at `http://127.0.0.1:3000`, its State backend at `:8001`, and FastAPI at `:8000`.

- Market Overview: route/H1, `#market-price`, `#market-source`, limitation text and no trade controls verified. Direct browser API request returned 200.
- Signals: route/H1 and authoritative empty state verified. Direct browser API request returned 200 with an empty typed page.
- Jobs: protected route rendered “Protected transport boundary required”; direct browser API request returned 401 `access_required`, proving fail-closed Feature-67 behavior without protected-content flash. Named job rows cannot be runtime-verified without an approved Device-bound PoP Session.
- Back/forward reconstructed Signals and Jobs routes.
- A 390×844 Market viewport had equal scroll/client width (390 px), proving no page-level horizontal overflow.
- Tab focus reached an anchor. Programmatic command-palette keyboard activation did not open the dialog and remains a browser limitation requiring Prompt-7 follow-up.
- Prompt-9 consumes HTTP only; WS cleanup is NOT_APPLICABLE. Route transition tests still verify canonical disconnect ownership.

## DTO-to-DOM lineage

- Jobs: `/api/v1/operations/jobs` → `BackgroundJobHealthOut.job_name/health_state/...` → `adapt_jobs` → `JobViewModel` → `JobsState` → `jobs_screen` → `.job-name/.job-status` and timing/failure text.
- Market: persisted `BTCPricePoint` → `/api/v1/market/overview` → `BTCMarketOverviewOut.price_usd/source/observed_at` → generated success DTO → `adapt_market_overview` → `MarketOverviewState` → `market_overview_screen` → named IDs.
- Signals: `Signal` repository → `/api/v1/signals/top` → `SignalOut.signal_type/severity/confidence/score/is_published/created_at` → `adapt_market_signals` → `MarketSignalsState` → `market_signals_screen` → named classes.

## Rollback

The typed Market overview endpoint, generator authorization, Prompt-9 models/adapters, States, screens, route metadata, lifecycle events, fixtures/tests, and this matrix can be reverted independently. Preserve Incidents/SLO, Stage-1 ownership, Feature-52’s four states, Features 58/67, and do not restore raw-dictionary Market State as canonical production ownership.
