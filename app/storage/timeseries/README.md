# TimescaleDB Foundation

This package is the initial TimescaleDB foundation for the Bitcoin Bastion Storage Layer. It prepares configuration, health checks, safe hypertable helpers, and base repository abstractions for later prompts.

## What TimescaleDB is used for

TimescaleDB is the future time-series store for:

- BTC price points;
- BTC candles;
- mempool fee snapshots;
- provider health snapshots;
- source health snapshots;
- metric usage time series;
- access integrity history;
- other append-oriented metrics and operational history.

## What TimescaleDB must not store

TimescaleDB must not become the transactional source of truth for:

- Access Certificates;
- Subscription Entitlements;
- payment/access authorization decisions;
- revocations;
- Recovery Quorums;
- treasury or policy decisions;
- seed phrases;
- Bitcoin private keys;
- wallet files;
- xprv/yprv/zprv material;
- raw Access Pass bearer tokens;
- raw API secrets.

PostgreSQL remains the transactional source of truth for critical state.

## Configuration variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `TIMESCALE_ENABLED` | `false` | Enables TimescaleDB health/status behavior. Disabled mode must not require TimescaleDB. |
| `TIMESCALE_URL` | empty | Optional future dedicated TimescaleDB URL. Empty means TimescaleDB may share the primary PostgreSQL connection. |
| `TIMESCALE_CREATE_EXTENSION` | `false` | Allows explicit helper/migration execution of `CREATE EXTENSION IF NOT EXISTS timescaledb`. Not enabled by default. |
| `TIMESCALE_SCHEMA` | `public` | Schema intended for future time-series tables. |
| `TIMESCALE_DEFAULT_CHUNK_INTERVAL` | `1 day` | Default chunk interval for future hypertables. |
| `TIMESCALE_HEALTH_TIMEOUT_SECONDS` | `2` | Intended timeout budget for health checks. |
| `TIMESCALE_RETENTION_DAYS` | empty | Optional retention-policy input for future prompts. |
| `TIMESCALE_COMPRESSION_ENABLED` | `true` | Future compression-policy feature flag. |
| `TIMESCALE_CONTINUOUS_AGGREGATES_ENABLED` | `true` | Future continuous-aggregate feature flag. |

## Degraded mode behavior

- `TIMESCALE_ENABLED=false`: the app runs without TimescaleDB and storage health reports TimescaleDB as disabled.
- `TIMESCALE_ENABLED=true` with a non-PostgreSQL local/test connection: storage health reports TimescaleDB as degraded instead of failing import/startup.
- `TIMESCALE_ENABLED=true` with PostgreSQL available and the TimescaleDB extension available: storage health can report `ok` for the Timescale foundation.
- `TIMESCALE_ENABLED=true` with unavailable TimescaleDB/extension checks: market, candle, metrics, and provider-health features may be degraded while critical transactional APIs continue to rely on PostgreSQL.

## Hypertable helpers

`hypertables.py` provides idempotent helper functions for later migrations or setup scripts:

- `ensure_timescale_extension(conn)`
- `create_hypertable_if_not_exists(conn, table_name, time_column, chunk_interval)`
- `set_compression_policy(conn, table_name, compress_after)`
- `set_retention_policy(conn, table_name, drop_after)`

All table names, column names, schemas, and intervals are validated before SQL is constructed. Do not pass user input directly to these helpers.

## Migration notes

This prompt does not add an Alembic migration that unconditionally creates the extension because the repository uses SQLite in local/test paths and TimescaleDB may not be installed in all PostgreSQL environments. Operators can use `ensure_timescale_extension` or a future environment-specific migration when `TIMESCALE_CREATE_EXTENSION=true` has been reviewed and approved.

## Backup and restore notes

Future TimescaleDB backup and restore procedures must validate hypertables, retention policies, compression policies, continuous aggregate refresh behavior, and restored time ranges. Until real time-series tables are migrated, Timescale evidence should remain `disabled`, `not_configured`, or `skipped` as appropriate.
