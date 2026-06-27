# ClickHouse Analytics Schema

## Purpose

Prompt 19/65 defines the initial ClickHouse analytics schema for Bitcoin Bastion. The schema is production-minded, privacy-bounded, and designed for rebuildable projections, but it does not ingest data or change runtime API behavior yet.

ClickHouse is an analytics warehouse and projection store. It must not be treated as transactional truth, authorization truth, payment truth, subscription truth, revocation truth, policy truth, recovery truth, or canonical audit-chain storage.

## Tables

| Table | Purpose |
| --- | --- |
| `market_time_machine_events` | Long-range market intelligence and historical replay events. |
| `news_impact_events` | News impact, market reaction windows, and source confidence history. |
| `candle_attribution_events` | Candle attribution and explanation of market moves. |
| `trace_runtime_events` | Privacy-safe Bastion Trace runtime behavior analytics. |
| `webhook_delivery_events` | Webhook delivery outcome and retry analytics. |
| `operator_replay_events` | Operator action timelines and incident/release replay analytics. |
| `api_usage_events` | SDK, MCP, CLI, quota, plan, and API usage analytics. |
| `analytics_schema_metadata` | Schema version and applied DDL metadata. |

## Source-of-Truth Boundary

Canonical truth remains in PostgreSQL, TimescaleDB, or Object Storage depending on the domain. ClickHouse receives rebuildable projections through future storage outbox workers. If ClickHouse is unavailable, critical transactional operations must continue when canonical stores are healthy; analytics and dashboards may degrade.

## Privacy Rules

ClickHouse DDL uses privacy-safe hashes and bounded labels. Do not project seed phrases, Bitcoin private keys, wallet files, `xprv` / `yprv` / `zprv`, raw access pass tokens, raw API keys, raw session tokens, raw payment identifiers, raw email addresses, raw Telegram IDs, raw IP addresses, raw Bitcoin addresses, webhook secrets, or raw endpoint URLs.

Trace analytics must use `address_hash` and `report_hash`. Webhook analytics must use `webhook_endpoint_hash`. API usage analytics must not store raw request bodies or raw response bodies in `payload_json`.

## Rebuild Strategy

Every analytics row must be rebuildable from canonical source stores or signed evidence. Projection workers introduced in later prompts must be idempotent, must preserve `projection_version` and `schema_version`, and must be able to replay from outbox checkpoints.

## Future Projection Workers

Prompt 20/65 will implement the outbox-to-ClickHouse projection worker and idempotent analytics ingestion path. Later prompts will add backfill/rebuild commands, health validation, and domain-specific analytics APIs.

## Degraded Mode

When ClickHouse is disabled or unavailable:

- storage health should report ClickHouse as disabled or degraded;
- Market Time Machine and long-range analytics may be unavailable or stale;
- dashboards must not claim fake freshness;
- PostgreSQL and TimescaleDB remain canonical for operational state;
- no access, revocation, subscription, payment, policy, or recovery decision may depend solely on ClickHouse.
