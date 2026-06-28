# Market Time Machine Analytics Service

This package contains the first ClickHouse-backed query layer for Bitcoin Bastion's Market Time Machine analytics.

ClickHouse is analytics/projection only. PostgreSQL, TimescaleDB, and Object Storage remain canonical truth. This service reads bounded ClickHouse projections and returns degraded-mode responses when ClickHouse is disabled, unavailable, or missing a projection.

The service does not ingest data, perform trading execution, provide financial advice, prove Bitcoin consensus state, or make access/subscription/payment/policy decisions.

## Query Limits

- Default window: 24 hours when no bounds are supplied.
- Default soft window: 365 days.
- Hard maximum window: 3650 days.
- Default limit: 500.
- Hard maximum limit: 5000.

## Supported Query Families

- Market event timeline.
- News impact history.
- Candle attribution history.
- Provider degradation history.
- Signal reliability history.
- Market regime transition history.
- Historical reaction windows.
