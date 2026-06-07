# Event Outbox

The Bitcoin Bastion Event Outbox is a durable internal persistence foundation for future event delivery. It stores domain events in the database before any external system can consume them.

This document covers persistence only. It does **not** implement webhook HTTP dispatch, WebSocket broadcasting, Telegram delivery, SDK consumers, CLI commands, MCP connectors, or plugin runtime execution.

## Why the Outbox Pattern Exists

The outbox pattern prevents domain services from coupling business changes directly to external delivery. Future domain services can record an event row in the same durable database layer used by the application. Later dispatcher workers can read pending rows and deliver them outward with retries, audit, and operator visibility.

```text
domain event
  ↓
event outbox row
  ↓
future dispatcher worker
  ↓
webhook / websocket / telegram / SDK / audit / plugin consumer
```

Prompt 5 stops at `event outbox row`.

## Table

The table is `event_outbox`.

| Field | Purpose |
| --- | --- |
| `id` | Internal integer primary key. |
| `event_id` | Stable UUID for the logical event; unique. |
| `event_type` | Canonical event type such as `signal.published` or `trace.report.created`. |
| `event_version` | Payload schema version; defaults to `1`. |
| `domain` | Canonical event domain from the event registry. |
| `aggregate_type` | Optional related entity type, such as `signal` or `trace_report`. |
| `aggregate_id` | Optional related entity identifier. |
| `payload_json` | JSON event payload, stored as text under the repository convention. |
| `metadata_json` | JSON event metadata after secret-like values are redacted. |
| `status` | Delivery lifecycle status. |
| `priority` | Integer priority; lower values are processed first by future dispatchers. |
| `attempts` | Number of recorded delivery attempts or failure cycles. |
| `max_attempts` | Maximum attempts before future dispatcher dead-letter handling; defaults to `5`. |
| `next_attempt_at` | Future dispatcher eligibility timestamp. |
| `locked_at` | Future dispatcher lock timestamp. |
| `locked_by` | Future dispatcher worker identity. |
| `last_error` | Sanitized error summary. |
| `created_at` | Row creation timestamp. |
| `updated_at` | Last row update timestamp. |
| `dispatched_at` | Timestamp when a future dispatcher marks delivery complete. |
| `dead_lettered_at` | Timestamp when an event is moved to dead-letter status. |

Indexes exist for event ID uniqueness, status, event type, domain, aggregate pair, retry scheduling, creation time, and status plus retry scheduling.

## Status Lifecycle

Normal path:

```text
pending
  ↓
locked
  ↓
dispatched
```

Failure path:

```text
pending
  ↓
locked
  ↓
failed
  ↓
pending
  ↓
locked
  ↓
dead_letter
```

Cancellation path:

```text
pending
  ↓
cancelled
```

Repository helpers implement basic transition checks. Stricter state-machine enforcement remains a follow-up for dispatcher prompts.

## Safety Rules

The outbox preserves the Bitcoin Bastion no-custody posture:

- no seed phrase handling;
- no mnemonic handling;
- no private key or extended private key handling;
- no wallet file handling;
- no signing-material handling;
- no transaction signing;
- no automatic treasury execution.

Payloads with obvious sensitive wallet/signing material are rejected before persistence. Metadata fields such as `authorization`, `api_key`, `secret_key`, token fields, and private-key fields are redacted to `[REDACTED]` before storage.

Payload JSON is limited to 64 KB. Metadata JSON is limited to 16 KB. Oversized input is rejected and not partially persisted.

## Relationship to Future Webhooks

The outbox prepares durable rows for webhook dispatch, but this task does not send HTTP requests, sign webhook payloads, create webhook subscription tables, or manage delivery logs. Future webhook prompts should read only eligible outbox rows and preserve registry metadata such as `webhook_allowed`.

## Relationship to Future WebSocket Streams

The outbox records events that future WebSocket streams may consume. This task does not add WebSocket routes, connection managers, broadcast loops, or stream authorization.

## Relationship to Future Audit and Replay

The outbox can support audit and replay surfaces because it stores event payloads, metadata, aggregate identifiers, status, attempts, and sanitized errors. It is not an immutable audit ledger by itself. Any WORM storage, long-term retention policy, replay certification, or compliance-grade audit workflow remains a later task.

## Limitations

- External delivery is not implemented.
- Retry execution is not implemented.
- Dispatcher locking is prepared but no worker consumes locks yet.
- Webhook, WebSocket, Telegram, SDK, CLI, MCP, and plugin integrations are future work.
- Public-safe publication must still consult the event registry before exposing any event outside the operator-controlled backend.
