# Analytics Store Package

This package contains the ClickHouse analytics-store foundation for Bitcoin Bastion.

## Role

ClickHouse is analytics/projection only. It is a rebuildable read-optimized warehouse for long-range market replay, event analytics, developer usage trends, webhook delivery analytics, operator replay, and future Market Time Machine workloads.

Canonical truth remains in:

- PostgreSQL for transactional state, access metadata, policies, subscriptions, revocations, and audit-chain truth.
- TimescaleDB for operational time-series state and bounded recent history.
- Object Storage for proof packets, evidence archives, signed reports, and artifact bytes.

## Projection Model

All ClickHouse writes must eventually come from controlled outbox/projection workers. Projections must be idempotent, versioned, and rebuildable from canonical sources. Route handlers must not write directly to ClickHouse and another canonical store in the same business operation.

Prompt 19 only defines the schema registry and SQL DDL files. It does not create projection workers, move production data, or change API behavior.

## Privacy and Safety Boundaries

Sensitive material must not be projected into ClickHouse:

- seed phrases;
- Bitcoin private keys;
- wallet files;
- `xprv`, `yprv`, or `zprv` material;
- raw Access Pass values;
- raw API keys;
- raw session tokens;
- raw payment identifiers;
- raw email addresses;
- raw Telegram IDs;
- raw IP addresses;
- raw Bitcoin addresses.

Use hashes or fingerprints such as `pass_lookup_hash`, `workspace_id_hash`, `device_id_hash`, `api_key_hash`, `session_id_hash`, `object_hash`, `address_hash`, `report_hash`, and `webhook_endpoint_hash`.

Trace analytics must use `address_hash` and `report_hash`, not raw Bitcoin addresses or raw report IDs. Webhook analytics must use `webhook_endpoint_hash`, not raw webhook URLs or secrets. API usage analytics must not store raw request or response bodies in `payload_json`.

## DDL Registry

`clickhouse_schema.py` exposes import-safe helpers:

- `CLICKHOUSE_DDL_FILES`
- `CLICKHOUSE_ANALYTICS_TABLES`
- `get_clickhouse_ddl_paths()`
- `get_clickhouse_table_names()`

These helpers do not require a live ClickHouse server and are safe for unit tests.
