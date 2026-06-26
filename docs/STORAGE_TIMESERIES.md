# Bitcoin Bastion Time-Series Storage

## Purpose

TimescaleDB is the operational time-series store for Bitcoin Bastion. It is used for append-oriented market and operational history that needs bounded time-window queries. PostgreSQL remains the transactional source of truth for access, entitlement, revocation, recovery, policy, artifact metadata, and outbox decisions.

This prompt makes the existing BTC market time-series tables Timescale-compatible without requiring TimescaleDB in local or SQLite test environments.

## Data that belongs in TimescaleDB

Initial hypertable candidates are:

| Table | Time column | Purpose |
| --- | --- | --- |
| `btc_price_points` | `observed_at` | Raw/normalized provider BTC price observations. |
| `btc_candles` | `open_time` | Operational OHLC candles used by market and intelligence services. |
| `mempool_fee_snapshots` | `observed_at` | Fee-market and mempool snapshot history for future fee analytics. |

Future candidates include provider health snapshots, source health snapshots, metric usage time series, access integrity history, and other append-only operational metrics.

## Plain PostgreSQL and SQLite fallback

When `TIMESCALE_ENABLED=false`:

- the app uses normal SQLAlchemy tables;
- the TimescaleDB extension is not required;
- local SQLite tests and lightweight development continue to work;
- storage health reports TimescaleDB as disabled;
- market APIs and tasks keep using the same models and repository boundary.

The migration creates normal relational indexes and the `mempool_fee_snapshots` table in a database-compatible way. Timescale-specific conversion is skipped outside PostgreSQL or when `TIMESCALE_ENABLED` is not enabled.

## Timescale-enabled behavior

When `TIMESCALE_ENABLED=true` in a PostgreSQL/TimescaleDB environment:

- `TIMESCALE_CREATE_EXTENSION=true` allows the migration/helper path to run `CREATE EXTENSION IF NOT EXISTS timescaledb`;
- if the extension is installed, the migration attempts `create_hypertable(..., if_not_exists => TRUE)` for the configured market time-series tables;
- storage health reports extension availability and hypertable status for `btc_price_points`, `btc_candles`, and `mempool_fee_snapshots`;
- critical transactional APIs must continue to rely on PostgreSQL truth, not TimescaleDB projections.

## Retention and compression

Retention and compression are prepared but not yet enabled as policy in this prompt. Later prompts should define table-specific settings such as:

- raw price point retention;
- candle retention by timeframe;
- mempool fee snapshot retention;
- compression after a safe historical window;
- continuous aggregate refresh policies if needed.

Retention must be documented and tested before deleting operational history.

## Relationship to ClickHouse

TimescaleDB and ClickHouse have different responsibilities:

- TimescaleDB = operational time-series store for bounded API/service queries.
- ClickHouse = future analytics warehouse for Market Time Machine, large replay, and long-range analytical projections.

Do not use ClickHouse for operational access decisions. Do not use TimescaleDB as the analytics warehouse for all historical replay.

## What this prompt implemented

- `mempool_fee_snapshots` SQLAlchemy model and migration table.
- Composite indexes for BTC price point and mempool time-window queries.
- Defensive migration logic that only prepares Timescale hypertables when PostgreSQL and `TIMESCALE_ENABLED=true` are present.
- `MarketTimeSeriesRepository` for bounded price point, candle, and mempool snapshot reads/writes.
- Storage health details for Timescale extension and hypertable status.

## What is intentionally not implemented yet

- No ClickHouse analytics projection.
- No Qdrant/vector memory integration.
- No full Market Time Machine warehouse migration.
- No removal of existing market models or public API contracts.
- No retention/compression policy activation.
- No claim that TimescaleDB is required for all deployments.

## Security rules

TimescaleDB must never store seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, raw API secrets, custody material, or unredacted sensitive material. Time-series tables must use bounded queries and must not introduce a global user identifier for privacy-sensitive domains.
