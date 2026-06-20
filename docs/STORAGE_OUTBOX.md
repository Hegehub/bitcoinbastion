# Storage Outbox

## Purpose

The Storage Outbox is the durable PostgreSQL foundation for future cross-storage projections. Domain services should write canonical PostgreSQL state and enqueue a `storage_outbox_events` row in the same transaction boundary. Later projector workers can safely project those events into TimescaleDB, ClickHouse, Qdrant/pgvector, Object Storage, Redis fanout, webhook/WebSocket delivery, SDK, MCP, and audit pipelines.

The outbox is durable. The outbox is stored in PostgreSQL. Projection targets are rebuildable.

## Why direct cross-database writes are forbidden

Route handlers and random services must not directly write to PostgreSQL, ClickHouse, TimescaleDB, Qdrant, Redis, and Object Storage in one ad hoc operation. That pattern hides partial failure, makes retry unsafe, and creates unclear source-of-truth ownership.

Correct pattern:

```text
Domain Service
→ canonical PostgreSQL transaction
→ storage_outbox_events row
→ background projector/dispatcher
→ future projections
```

ClickHouse, Qdrant, TimescaleDB, Redis, Object Storage, webhook, WebSocket, SDK, and MCP projections must be written by projectors, not route handlers.

## Event schema

A storage outbox event records:

- stable `event_id`;
- `event_type`;
- `aggregate_type`, `aggregate_id`, and optional `aggregate_version`;
- JSON object `payload_json` and `metadata_json`;
- non-empty `target_stores` list;
- optional unique `idempotency_key`;
- status, priority, retry count, max retries, lock fields, availability time, error summary, processed time, and timestamps.

## Lifecycle

```text
pending
→ processing
→ processed
```

Retry path:

```text
pending/retry
→ processing
→ retry
→ processing
→ processed
```

Failure paths:

```text
processing → failed
processing → dead_letter
processing → retry → dead_letter
```

Cancellation is reserved for future operator workflows.

## Status meanings

- `pending`: ready to be claimed when `available_at <= now`.
- `processing`: claimed by a worker with `locked_by` and `locked_at`.
- `processed`: projection workflow completed.
- `retry`: retryable failure; available later according to backoff.
- `failed`: permanent failure that should not be retried by default.
- `dead_letter`: retry budget exhausted or explicitly dead-lettered.
- `cancelled`: reserved for future operator cancellation.

Failed projections must not silently disappear. Dead-letter events must be observable.

## Idempotency rules

`enqueue_once` and repository `create_event` respect `idempotency_key`. If an event already exists for the same key, the existing event is returned instead of creating a duplicate.

## Retry and dead-letter behavior

The service uses deterministic bounded backoff:

```text
delay_seconds = min(3600, 2 ** retry_count * 30)
```

When retry budget is exhausted, events move to `dead_letter`. Errors are sanitized so known secret-like terms are not persisted.

## Future projection targets

Initial target store values include:

- `timescale`
- `clickhouse`
- `qdrant`
- `pgvector`
- `object_storage`
- `redis`
- `webhook`
- `websocket`
- `sdk`
- `mcp`
- `audit`

Redis is not durable truth. Redis projection is for ephemeral state or fanout only.

## Degraded mode behavior

If future projection targets are unavailable, canonical PostgreSQL writes may still succeed if product policy allows. Outbox rows remain durable and retryable. Projection lag, failed rows, and dead-letter rows must be visible to operators.

## Security and privacy

Outbox events must not contain seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw secrets, raw access tokens, or bearer Access Pass secrets in `payload_json` or `metadata_json`.

Prefer hashes, fingerprints, stable IDs, redacted metadata, and references to canonical PostgreSQL rows or Object Storage artifacts.

## Examples

```python
outbox.enqueue_event(
    event_type="trace.report.created",
    aggregate_type="trace_report",
    aggregate_id=str(report_id),
    payload_json={"report_id": str(report_id)},
    target_stores=["clickhouse", "websocket"],
)
```

## What not to do

- Do not write directly to ClickHouse, TimescaleDB, Qdrant, Redis, Object Storage, or webhooks from route handlers.
- Do not mark an event processed before projection succeeds.
- Do not hide failures in logs only.
- Do not store sensitive Bitcoin, wallet, access-token, or secret material in payloads.
- Do not treat Redis as durable truth.
- Do not claim prompt 6 implements real projection workers.
