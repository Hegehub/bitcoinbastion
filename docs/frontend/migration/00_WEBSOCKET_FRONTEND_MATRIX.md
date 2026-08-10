# WebSocket Frontend Matrix

The nine channels use backend-owned `bitcoin-bastion.events` wire version 1 and one canonical frontend transport owner. Payloads are bounded, sanitized JSON facts inside a strict discriminated envelope; the payload map is explicitly the event-outbox compatibility boundary, not an unreviewed `Any` fallback.

| Channel family | Message/auth contract | Reconnect and fallback | Owner/prompt |
|---|---|---|---|
| events | v1 system/error/heartbeat/event; all supported topics | bounded reconnect; replay explicitly unavailable; current HTTP refresh on gap | Core, `P1R2-B05`, resolved |
| signals | v1 specialized event types | stale on loss; matching HTTP read | Market, `P1R2-B06`, resolved |
| news | v1 specialized event types | stale on loss; matching HTTP read | Market, `P1R2-B07`, resolved |
| onchain | v1 public advisory events | stale age and HTTP fallback | Core, `P1R2-B08`, resolved |
| market | v1 specialized event types | coalesce rendering, retain event identity | Market, `P1R2-B09`, resolved |
| trace | v1 public-data advisory events | HTTP refresh; disagreement/partial preserved | Trace, `P1R2-B10`, resolved |
| treasury | v1 advisory notification stream; no execution messages | disconnect disables mutation affordances | Console, `P1R2-B11`, resolved |
| provider-health | v1 limited advisory payload | verified live connection harness and HTTP fallback | Operations, `P1R2-B12`, resolved |
| intelligence-timeline | v1 specialized event types | stale on loss; HTTP refresh | Market, `P1R2-B13`, resolved |

No channel may transport signing material, one-time credentials, recovery factors or rejected sensitive input. `last_event_id` replay is explicitly unavailable in the current backend.

Ordering is by unique `event_id` identity; timestamps are not treated as a total order. Duplicate IDs are suppressed in a bounded 128-ID window. Because replay authority does not exist, suspected gaps or reconnects mark the view degraded and trigger a current authoritative HTTP refresh rather than fabricating events. Wire v1 accepts only v1; unknown versions fail closed. Breaking required-field, discriminator, unit, timestamp, or ordering changes require a new wire version.
