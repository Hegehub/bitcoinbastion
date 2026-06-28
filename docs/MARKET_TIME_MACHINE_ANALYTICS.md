# Market Time Machine Analytics Query Layer

## Purpose

The Market Time Machine analytics query layer provides bounded historical analytics reads for market events, news impact, candle attribution, provider degradation, signal reliability, market regime transitions, and reaction windows.

ClickHouse is analytics/projection only. PostgreSQL, TimescaleDB, and Object Storage remain canonical truth depending on the domain. This layer does not ingest data, move product truth, execute trades, provide financial advice, or prove Bitcoin consensus state.

## Supported Queries

- `GET /api/v1/market-time-machine/events`
- `GET /api/v1/market-time-machine/news-impact`
- `GET /api/v1/market-time-machine/candle-attribution`
- `GET /api/v1/market-time-machine/provider-degradation`
- `GET /api/v1/market-time-machine/signal-reliability`
- `GET /api/v1/market-time-machine/regime-transitions`
- `GET /api/v1/market-time-machine/reaction-windows`

All route handlers parse request parameters and delegate to `MarketTimeMachineAnalyticsService`. SQL construction lives in `app/services/market_time_machine/queries.py`.

## Query Limits

- Default query window: 24 hours when no range is supplied.
- Soft/default maximum: 365 days.
- Hard maximum: 3650 days.
- Default limit: 500 rows.
- Hard maximum limit: 5000 rows.

Requests larger than the hard maximum return a degraded response instead of running an unbounded query.

## Degraded Mode

If ClickHouse is disabled, responses use:

```json
{"runtime_mode":"disabled","source_store":"none","items":[]}
```

If ClickHouse is configured but unavailable, responses use:

```json
{"runtime_mode":"unavailable","source_store":"none","items":[]}
```

If a requested projection/table is missing, responses use:

```json
{"runtime_mode":"degraded","source_store":"clickhouse","items":[]}
```

No endpoint should claim fake freshness when ClickHouse projections are stale or missing.

## Storage Responsibility

ClickHouse stores rebuildable projections populated by outbox workers. It is not an authorization, payment, subscription, revocation, recovery, policy, or canonical audit store.

## Security Boundaries

Do not store, log, embed, or expose seed phrases, private keys, wallet files, `xprv` / `yprv` / `zprv`, raw access tokens, or raw Access Pass material. Query parameters are bounded and passed through parameterized query builders.

## Future Extensions

Later prompts may add projection freshness checks, richer Market Time Machine APIs, evidence-linked replay workflows, and optional frontend/SDK/MCP consumers.
