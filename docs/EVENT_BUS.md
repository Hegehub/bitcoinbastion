# Event Bus

The Bitcoin Bastion Event Bus is an internal publishing API that validates and records canonical events into the durable Event Outbox. It connects the event taxonomy and registry to the outbox persistence layer without performing any external delivery.

## What It Is

- An internal API for publishing registered Bitcoin Bastion events.
- A validation layer for event type, domain metadata, payload safety, metadata safety, and JSON serialization.
- A durable outbox writer that records events with `pending` outbox status.
- A future-compatible contract for webhook, WebSocket, Telegram, SDK, CLI, MCP, audit, and plugin consumers.

## What It Is Not

The Event Bus does **not**:

- send webhooks;
- open WebSocket connections;
- call Telegram;
- execute external HTTP delivery;
- move funds;
- sign transactions;
- handle seed phrases, private keys, wallet files, extended private keys, or signing material;
- replace dispatcher workers planned for later prompts.

## Publishing API

Use the internal publisher:

```python
from app.events import publish_event

result = publish_event(
    "signal.created",
    {"signal_id": 123, "confidence": 0.72, "limitations": ["correlation_not_causation"]},
    aggregate_type="signal",
    aggregate_id=123,
    source="signal_governance",
)
```

The result is an `EventPublishResult` with conservative status values:

```text
published_to_outbox
duplicate_ignored
rejected
```

`published_to_outbox` means the event was durably recorded as an outbox row. It does not mean webhook, WebSocket, Telegram, SDK, CLI, MCP, audit, or plugin delivery occurred.

## Why Events Go to Outbox First

Events go to the database-backed outbox before any external delivery so domain services do not couple business changes directly to integrations. This preserves durability and lets future workers handle retries, locks, dead-letter behavior, rate limits, and operator review.

```text
domain service
  ↓
publish_event(...)
  ↓
Event Bus validation and serialization
  ↓
event_outbox row with status pending
  ↓
future dispatcher prompts
```

## Validation and Serialization

The Event Bus validates that:

- `event_type` is registered in the event registry;
- payloads are JSON-serializable;
- payloads are deterministically serialized with stable key ordering;
- datetime, UUID, Decimal, and date values serialize safely;
- unsupported complex objects fail clearly;
- payload hashes are stable for the same logical payload;
- aggregate/source/idempotency strings are safety-checked when present.

## Metadata

Every published event stores metadata fields where possible:

```text
event_type
event_version
aggregate_type
aggregate_id
source
actor_id
correlation_id
idempotency_key
created_at
payload_hash
```

If no `correlation_id` is provided, one is generated. Metadata is persisted in the outbox row after redaction and safety validation.

## Idempotency

If `idempotency_key` is provided, repeated publishing with the same `event_type` and key returns `duplicate_ignored` and reuses the existing outbox event reference instead of creating another pending row. This is a local database-level convenience, not a distributed locking system.

## Safety Rules

The Event Bus preserves Bitcoin Bastion no-custody constraints:

- payloads and metadata are inspected before persistence;
- obvious seed phrase, mnemonic, recovery phrase, private key, xprv, yprv, zprv, wallet file, keystore, and signing-material references are rejected;
- secret-like metadata keys such as authorization headers and API keys are redacted before storage;
- raw payloads are not included in bounded publish logs;
- Trace events remain advisory-only and not legal verification;
- market and signal events remain informational and not financial advice.

## Examples

### Signal

```python
publish_event(
    "signal.created",
    {"signal_id": 123, "confidence": 0.72, "limitations": ["correlation_not_causation"]},
    aggregate_type="signal",
    aggregate_id=123,
    source="signal_governance",
)
```

### Trace

```python
publish_event(
    "trace.report.created",
    {
        "report_id": 55,
        "address": "bc1qexamplepublicaddress000000000000000000000",
        "trace_band": "medium",
        "advisory_only": True,
        "not_legal_verification": True,
        "not_consensus_proof": True,
        "no_custody": True,
    },
    aggregate_type="trace_report",
    aggregate_id=55,
    source="bastion_trace",
)
```

### Provider Health

```python
publish_event(
    "provider.degraded",
    {"provider_name": "market_provider", "reason": "stale_data", "degraded": True},
    aggregate_type="provider_health",
    aggregate_id="market_provider",
    source="provider_health",
)
```

## Future Connections

Future prompts may add dispatcher workers that consume `event_outbox` rows for webhooks, WebSocket streams, SDK consumers, MCP connectors, plugin systems, Telegram delivery, or audit/replay surfaces. Those future layers must continue to consult registry metadata, preserve public-safe boundaries, and keep degraded/fallback/stale limitations visible.
