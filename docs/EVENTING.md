# Eventing System

This document consolidates the event-related documentation from `EVENTS.md`, `EVENT_BUS.md` and `EVENT_OUTBOX.md`. It explains the structure of events, the publishing API, and the outbox pattern.

## Event Model

Bitcoin Bastion events are stable, typed contracts for internal and external integrations. Events follow a naming convention of `domain.entity.action` using lowercase and dot‑separated names. Each event uses a base envelope with fields such as `event_id`, `event_type`, `event_version`, `domain`, `source_module`, timestamps, aggregate identifiers, actor details, payload, limitations and safety flags.

Canonical event domains include `news`, `signal`, `trace`, `wallet`, `treasury`, `policy`, `market`, `observability`, `provider`, `evidence` and `system`. Events are catalogued with metadata describing visibility, severity, webhook and WebSocket eligibility, audit status and whether they are public‑safe.

Safety flags such as `advisory_only`, `not_financial_advice`, `no_custody` and `correlation_not_causation` indicate how consumers should interpret the event. Payload safety rules forbid seed phrases, private keys, wallet files and other signing material in event payloads.

## Event Bus

The Event Bus is an internal API for publishing registered events. It validates event types, payloads and metadata, enforces JSON serialization, and writes rows to the durable Event Outbox. The bus does not dispatch webhooks, open WebSocket connections or sign transactions.

Publishing an event returns a result indicating whether it was recorded, ignored as a duplicate or rejected. Validation ensures event types are registered, payloads are JSON‑serializable, datetime and decimal values are properly encoded and idempotency keys prevent duplicate rows. The bus enforces no‑custody rules by inspecting payloads and metadata for seed phrases, private keys, authorization headers and other secrets.

## Event Outbox

The Event Outbox is a database table that stores events before any external delivery occurs. The outbox pattern decouples business changes from delivery, enabling future workers to retry delivery, enforce rate limits, handle dead‑letter queues and provide operator visibility.

Each outbox row records the event ID, type, version, domain, aggregate identifiers, payload JSON, metadata JSON and status fields such as `pending`, `locked`, `dispatched`, `failed`, `cancelled` or `dead_letter`. The status lifecycle guides dispatcher workers and includes idempotency and cancellation behaviours.

Safety rules prohibit sensitive material in payloads or metadata. Payloads are limited to 64 KB and metadata to 16 KB, with oversized inputs rejected. The outbox does not implement external delivery; future workers will handle webhooks, WebSocket streams, Telegram messages, SDK and CLI consumers, MCP connectors and plugin notifications.

## Putting It Together

When a service publishes an event:

1. The Event Bus validates and serializes the event, rejecting unsafe payloads or unknown types.
2. The event is recorded in the `event_outbox` table with status `pending` and associated metadata.
3. Future dispatcher workers will consume pending rows and deliver them via configured transports such as webhooks or WebSocket streams.

This architecture ensures durability, safety and auditability of events while keeping delivery and execution separate from core business logic.
