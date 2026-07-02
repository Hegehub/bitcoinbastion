# Event bus

Owns domain events, outbox persistence, internal event dispatch, webhook delivery and event taxonomy.

Current canonical paths:

- `app/services/events/`
- webhook and WebSocket endpoints under `app/api/v1/`

Migration rule: events must be versioned or backward-compatible, idempotent for consumers and auditable when they affect operator workflows.
