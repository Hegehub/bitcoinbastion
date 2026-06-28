# Source Health & Provider Confidence

Tracks per-check provider outcomes, confidence deltas, degraded/backoff state, and time-window snapshots.

Why this exists: evidence quality depends on provider reliability, not claims.

## Provider and Source Health Time-Series Storage

Source and provider definitions remain canonical in PostgreSQL. Prompt 15 adds TimescaleDB-compatible history tables for source health snapshots, provider health snapshots, source confidence events, and provider confidence events. These tables preserve historical observations such as `observed_at`, `domain`, `status`, `health_score`, `confidence_score`, latency, error rate, success/failure counts, degraded reason, runtime mode, and bounded metadata.

Redis may cache current source status, nonce/challenge state, or fanout coordination, but Redis is not a source of truth for source health history. If Redis is lost, caches rebuild from PostgreSQL and the historical time-series tables.

If TimescaleDB is disabled, the tables remain normal PostgreSQL-compatible tables. If TimescaleDB is enabled, `observed_at` is the hypertable time column. If TimescaleDB becomes unavailable, current checks may still run, but historical dashboards and reports should show degraded mode.

Security boundaries:

- Do not store seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv, API secrets, raw auth headers, private provider credentials, or tokenized URLs in source health metadata.
- Use bounded labels such as provider/source keys, source type, domain, and status.
- Future ClickHouse analytics must be populated through projectors/outbox paths, not direct route-handler writes.
