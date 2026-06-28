# TimescaleDB Operations

## Purpose

TimescaleDB stores operational time-series data for BTC prices/candles, mempool fee snapshots, provider/source health, metric usage, and access-integrity history. Prompt 17 adds operational maturity: continuous aggregate definitions, retention policy configuration, compression policy configuration, status checks, validation scripts, and rebuild guidance.

## Hypertables and Continuous Aggregates

Expected continuous aggregate groups:

- `btc_price_1m`, `btc_price_5m`, `btc_price_1h`, `btc_price_1d`
- `btc_candles_5m`, `btc_candles_1h`, `btc_candles_1d`
- `provider_health_5m`, `provider_health_1h`, `provider_health_1d`
- `source_health_1h`, `source_health_1d`
- `metric_usage_5m`, `metric_usage_1h`, `metric_usage_1d`
- `access_integrity_1h`, `access_integrity_1d`

The migration creates these only when PostgreSQL, `TIMESCALE_ENABLED=true`, and the TimescaleDB extension are available. Local SQLite and plain test environments skip Timescale-only SQL.

## Retention Policy

Retention is controlled by:

- `TIMESCALE_RETENTION_ENABLED`
- `TIMESCALE_RAW_MARKET_RETENTION_DAYS`
- `TIMESCALE_RAW_HEALTH_RETENTION_DAYS`
- `TIMESCALE_RAW_USAGE_RETENTION_DAYS`
- `TIMESCALE_AGGREGATE_RETENTION_DAYS`
- `TIMESCALE_ACCESS_HISTORY_RETENTION_DAYS`

Raw high-volume operational data may expire earlier than aggregates. Retention must never delete canonical PostgreSQL audit truth, Access Certificates, Subscription Entitlements, Payment Proofs, Revocation Records, Recovery Quorums, or Policy Rules.

## Compression Policy

Compression is controlled by:

- `TIMESCALE_COMPRESSION_ENABLED`
- `TIMESCALE_COMPRESS_AFTER_DAYS`
- `TIMESCALE_COMPRESS_MARKET_AFTER_DAYS`
- `TIMESCALE_COMPRESS_HEALTH_AFTER_DAYS`
- `TIMESCALE_COMPRESS_USAGE_AFTER_DAYS`

Compression applies to older hypertable chunks for market, health, and usage tables. Operators can disable compression globally with `TIMESCALE_COMPRESSION_ENABLED=false`.

## Refresh and Rebuild Strategy

Continuous aggregates are rebuildable from raw Timescale hypertables. Operators can inspect aggregate/policy status with:

```bash
scripts/timescale-validate-policies.sh
```

Refresh mutations are intentionally not exposed through an unauthenticated API. Use `TimescaleOperationsService.refresh_all_recent()` from an authenticated operator shell or a controlled maintenance job.

## Degraded Mode

If TimescaleDB is unavailable:

- critical access/auth/payment/policy operations must continue when PostgreSQL is healthy;
- metrics, candles, usage history, provider/source health history, and dashboards may degrade;
- no endpoint should claim fake freshness;
- `/api/v1/storage/timescale/status` reports disabled/degraded status without secrets.

## Backup and Restore Implications

Backups should include raw hypertables and continuous aggregate definitions. Restore drills must validate raw time ranges, aggregate existence, retention jobs, compression jobs, and recent refresh behavior.

## Future ClickHouse Relationship

TimescaleDB is the operational time-series store. ClickHouse begins in Prompt 18 as the analytics warehouse for long-range replay and large scans. ClickHouse projections must be rebuildable and must not become transactional truth.

## Known Limitations

The default test suite does not require a live TimescaleDB instance. Real extension, policy, and aggregate refresh validation should be run in a dedicated Timescale integration environment.
