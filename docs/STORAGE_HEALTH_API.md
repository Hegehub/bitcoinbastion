# Storage Health API

## Purpose

`GET /api/v1/storage/status` is an operational status endpoint for the Bitcoin Bastion Storage Layer. It reports configured state, health, required/optional role, degraded-mode impact, and future-store implementation status for the multi-database roadmap.

This endpoint is not a marketing endpoint and is not a replacement for existing liveness/readiness checks unless explicitly adopted by operations policy.

## Endpoint

```http
GET /api/v1/storage/status
```

The response includes these store keys:

- `postgres`
- `redis`
- `object_storage`
- `timescale`
- `clickhouse`
- `qdrant`
- `sqlite_local`
- `duckdb_local`

## Status Values

| Status | Meaning |
| --- | --- |
| `ok` | The configured check completed successfully. |
| `disabled` | The store is disabled by configuration. |
| `degraded` | The store is reachable but operating in a reduced state. |
| `unavailable` | The store is configured but the check failed. |
| `misconfigured` | Required configuration is missing or inconsistent. |
| `not_configured` | No configuration exists for a required check. |
| `not_implemented` | The engine is planned or enabled, but this prompt does not implement its client/check. |
| `unknown` | The check cannot classify the state safely. |

## Roles

| Role | Meaning |
| --- | --- |
| `required` | Failure affects critical operational readiness for the current profile. |
| `optional` | Failure degrades features but does not necessarily stop critical operations. |
| `future` | Store is part of the storage roadmap. It may have foundation health checks before domain data is migrated. |
| `local_only` | Store applies to local/offline future features and must not fail server readiness by itself. |

## Degraded Mode Behavior

- PostgreSQL unavailable: critical operations are unavailable.
- Redis unavailable: cache, rate limits, queues, and websocket fanout may run in reduced mode; Redis is not durable truth.
- Object Storage unavailable: proof packet downloads, evidence exports, and signed artifact workflows may be unavailable.
- TimescaleDB disabled, degraded, or unavailable: time-series metrics, candles, and provider health history may be unavailable; transactional truth remains in PostgreSQL.
- ClickHouse disabled or not implemented: Market Time Machine and long-range analytics may be unavailable.
- Qdrant disabled or not implemented: semantic memory and similarity search may be unavailable.
- SQLite/DuckDB not implemented: local/offline operational and analytics features are unavailable, but server readiness is not failed by those stores alone.

## Security Redaction Rules

The endpoint must not expose:

- Raw database URLs.
- Passwords.
- Access keys or secret keys.
- Object Storage credentials.
- Internal tokens.
- Full exception traces.
- Private network topology.
- User identifiers, raw IP addresses, wallet addresses, seed phrases, private keys, `xprv`/`yprv`/`zprv`, API tokens, or raw Access Pass values.

Errors are returned as sanitized classes, for example:

```json
{
  "connection": "failed",
  "error_class": "OperationalError"
}
```

## Future Stores

TimescaleDB now has an initial foundation health check, but no domain tables have been migrated. ClickHouse, Qdrant, SQLite, and DuckDB may report `disabled` or `not_implemented` until their dedicated prompts add real clients and health checks. A disabled, degraded, or future store must not be described as production-ready.
