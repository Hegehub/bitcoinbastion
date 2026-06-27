# ClickHouse Projection Worker

## Purpose

The ClickHouse projector copies supported `storage_outbox_events` into ClickHouse analytics tables. ClickHouse is projection-only and rebuildable; PostgreSQL, TimescaleDB, and Object Storage remain canonical depending on the domain.

## Event Families

Prompt 20 supports these outbox event families:

- `market.time_machine.event`
- `news.impact.event`
- `candle.attribution.event`
- `trace.runtime.event`
- `webhook.delivery.event`
- `api.usage.event`
- `operator.replay.event`
- `provider.health.event`

The worker only selects outbox rows targeted to `clickhouse` with `pending` or retry status, available for processing, and below the max retry limit.

## Idempotency Strategy

Each projected row receives a deterministic `projection_id` used as the ClickHouse `event_id`:

```text
sha256(event_type || aggregate_type || aggregate_id || outbox_event_id)
```

This makes retries and replays stable. Future ClickHouse table engines or projection workers may add stronger deduplication, but the logical projection key is stable now.

## Retry and Failure Behavior

- Invalid or unsafe payloads are marked terminal failed.
- Unsupported event types are marked terminal failed.
- ClickHouse disabled mode returns a disabled summary without claiming events.
- ClickHouse insert failures are retryable and increment the outbox retry count.
- Outbox status is marked processed only after the ClickHouse insert succeeds.
- Dry runs fetch and map events but do not insert or update outbox state.

Projection failures must be visible. They must not be hidden or treated as successful analytics freshness.

## Running the Worker

Celery task name:

```text
storage.project_clickhouse_events
```

Parameters:

```text
batch_size=100
event_type=None
max_runtime_seconds=30
dry_run=False
```

Dry-run example:

```python
project_clickhouse_events.delay(batch_size=100, dry_run=True)
```

## Inspecting Backlog

Inspect `storage_outbox_events` for rows with target store `clickhouse`, status `pending` or retry, and `retry_count < max_retries`. Existing storage health should report ClickHouse disabled/degraded status separately.

## What Not To Store

Do not project Bitcoin seed phrases, Bastion Recovery Seed phrases, private keys, wallet files, `xprv` / `yprv` / `zprv`, raw access pass tokens, raw session tokens, raw API keys, authorization headers, payment secrets, or unencrypted recovery material.

If payloads contain forbidden material, the projector terminal-fails the event with sanitized error details.

## Degraded Mode

If ClickHouse is unavailable, transactional operations remain governed by canonical stores. Analytics dashboards and Market Time Machine queries may be stale or unavailable. Operators can replay from the outbox after ClickHouse recovers.
