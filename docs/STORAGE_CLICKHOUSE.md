# Bitcoin Bastion ClickHouse Analytics Store

## Purpose

ClickHouse is introduced as the future analytics warehouse for rebuildable projections, historical query acceleration, Market Time Machine workloads, large event/replay analytics, and operator reporting.

PostgreSQL and TimescaleDB remain canonical for operational truth. ClickHouse must never become the transactional source of truth for Access Certificates, Subscription Entitlements, policy rules, revocations, recovery quorums, payment proof, or custody decisions.

## What ClickHouse May Store

Future prompts may project rebuildable analytics rows such as:

- `market_time_machine_events`
- `news_impact_events`
- `candle_attribution_events`
- `trace_runtime_events`
- `webhook_delivery_events`
- `operator_replay_events`
- `api_usage_events`

Prompt 19 adds DDL files for these tables, but no production projector or data migration is created yet.

## What ClickHouse Must Not Store

ClickHouse must not store seed phrases, Bitcoin private keys, wallet files, `xprv` / `yprv` / `zprv`, raw access tokens, raw Access Pass values, raw API secrets, private provider credentials, or unredacted sensitive payloads.

ClickHouse must not be used for access-control decisions, revocation decisions, payment finality, subscription entitlement truth, recovery quorum truth, or policy-engine truth.

## Configuration

Required settings are available with safe disabled defaults:

```env
CLICKHOUSE_ENABLED=false
CLICKHOUSE_URL=http://localhost:8123
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=bitcoin_bastion
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_SECURE=false
CLICKHOUSE_CONNECT_TIMEOUT_SECONDS=5
CLICKHOUSE_QUERY_TIMEOUT_SECONDS=15
CLICKHOUSE_INSERT_TIMEOUT_SECONDS=30
CLICKHOUSE_MAX_RETRIES=2
CLICKHOUSE_PROFILE=disabled
```

Supported profiles are `disabled`, `development`, `single_node`, `staging`, `production`, and `enterprise`.

## Disabled Mode

When `CLICKHOUSE_ENABLED=false`, Bitcoin Bastion starts normally. The analytics store factory returns `DisabledAnalyticsStore`; health reports `enabled=false` and `status=disabled`; query and insert calls raise a clear disabled-store error.

ClickHouse is not required for application liveness. If enabled and unavailable, it may degrade analytics readiness and dashboards, but critical transactional operations remain governed by PostgreSQL and TimescaleDB health.

## Health Behavior

`GET /api/v1/storage/status` includes a `clickhouse` store entry. Disabled deployments report a disabled ClickHouse status without secrets. Enabled deployments perform a lightweight `SELECT 1` health check through the analytics-store abstraction.

## Projection and Rebuild Model

The intended model is:

```text
PostgreSQL / TimescaleDB = canonical write path
Storage Outbox = reliable event handoff
ClickHouse = rebuildable analytics projection
```

Prompt 19 adds the initial ClickHouse schema files. Future prompts will add projection workers, backfill/rebuild commands, and analytics APIs. All ClickHouse rows must be rebuildable from canonical stores or object-storage evidence.

## Security Constraints

- Do not log ClickHouse passwords or URLs with credentials.
- Do not include raw SQL text or row payloads in operational errors.
- Use bounded labels for future metrics: `operation`, `status`, and `profile`.
- Do not use unbounded or sensitive labels such as user IDs, addresses, report IDs, API keys, raw SQL, or table names from untrusted input.
