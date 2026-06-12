# WebSockets

Bitcoin Bastion exposes a generic operator-safe WebSocket event stream and domain-specific filtered streams. WebSocket delivery reuses the Event Bus, Event Outbox, serialization, sanitization, and in-process broker foundation; it does not create a second event system.

## Routes

Generic stream:

```text
/api/v1/ws/events
/api/v1/ws/events?topics=signals,trace,market
```

Specialized streams:

```text
/api/v1/ws/signals
/api/v1/ws/news
/api/v1/ws/onchain
/api/v1/ws/market
/api/v1/ws/trace
/api/v1/ws/treasury
/api/v1/ws/provider-health
/api/v1/ws/intelligence-timeline
```

Example client:

```js
const ws = new WebSocket("ws://localhost:8000/api/v1/ws/signals");

ws.onmessage = (msg) => {
  const event = JSON.parse(msg.data);
  console.log(event.event_type, event.data);
};
```

## Current status

The WebSocket layer is implemented as a single-process, in-memory broker foundation. Events are persisted through the Event Outbox first, and the in-process broker broadcasts sanitized event envelopes to currently connected clients. Distributed fanout with Redis/pubsub or another multi-instance coordination layer is future work.

WebSocket authentication and rate limiting are not production-grade in this build. Treat public-safe market, news, and provider-health feeds differently from operator/private streams such as trace, treasury, signals, onchain watchlist data, and intelligence timeline data until an explicit production auth layer is attached.

## Generic stream query parameters

- `topics`: optional comma-separated list. If omitted, the client subscribes to all supported topics.
- `limit_payload`: optional boolean, defaults to `true`. When enabled, payloads are sanitized and bounded.
- `heartbeat_seconds`: optional integer, defaults to `30`, clamped between `10` and `120`.
- `last_event_id`: accepted for future replay support. Replay is not available in this build; clients receive a `replay.not_available` system message.

Specialized routes support `limit_payload` and `heartbeat_seconds`. They do not accept arbitrary topics; each route has a fixed event allowlist.

## Supported topics

```text
signals
trace
market
news
onchain
treasury
policy
wallet
evidence
provider-health
observability
intelligence-timeline
```

Unknown event types are mapped to `observability` and include `metadata.unknown_event_type = true`.

## Specialized stream mapping

| Route | Event types |
| --- | --- |
| `/api/v1/ws/signals` | `signal.created`, `signal.published`, `signal.suppressed`, `signal.operator_review_required`, `signal.confidence_changed` |
| `/api/v1/ws/news` | `news.article.created`, `news.article.scored`, `news.event.created`, `news.event.high_impact` |
| `/api/v1/ws/onchain` | `onchain.large_transfer`, `onchain.watchlist_hit`, `onchain.fee_spike`, `onchain.mempool_pressure` |
| `/api/v1/ws/market` | `market.price_tick`, `market.candle_closed`, `market.regime.changed`, `market.candle.attributed`, `market.provider_confidence_changed` |
| `/api/v1/ws/trace` | `trace.report.created`, `trace.report.progress`, `trace.risk_band.changed`, `trace.batch.completed`, `trace.source_disagreement.updated`, `trace.evidence.updated` |
| `/api/v1/ws/treasury` | `treasury.request.created`, `treasury.approval.required`, `treasury.request.approved`, `treasury.request.rejected`, `treasury.policy.failed`, `treasury.psbt_status.changed` |
| `/api/v1/ws/provider-health` | `provider.degraded`, `provider.recovered`, `provider.stale`, `pipeline.lag.high`, `job.failed`, `job.recovered` |
| `/api/v1/ws/intelligence-timeline` | `intelligence.timeline.item.created`, `intelligence.timeline.item.updated`, `market.candle.attributed`, `news.event.high_impact`, `signal.published`, `evidence.packet.created` |

## Event envelope

All event messages include the standard fields required by generic and specialized streams. `payload` is retained as a compatibility alias for `data`.

```json
{
  "type": "event",
  "event_id": "evt_...",
  "event_type": "signal.published",
  "domain": "signals",
  "topic": "signals",
  "version": 1,
  "occurred_at": "2026-06-08T12:00:00Z",
  "published_at": "2026-06-08T12:00:01Z",
  "data": {},
  "limitations": [],
  "degraded": false,
  "stale": false,
  "payload": {},
  "metadata": {
    "source": "bitcoin_bastion",
    "advisory_only": true,
    "no_custody": true,
    "degraded": false,
    "stale": false,
    "fallback": false
  }
}
```

## System envelope

```json
{
  "type": "system",
  "event_type": "connection.accepted",
  "stream": "signals",
  "topics": ["signals"],
  "event_types": ["signal.created", "signal.published"],
  "message": "Connected to Bitcoin Bastion event stream."
}
```

## Heartbeat envelope

```json
{
  "type": "heartbeat",
  "event_type": "heartbeat",
  "timestamp": "2026-06-08T12:00:30Z"
}
```

## Error envelope

```json
{
  "type": "error",
  "event_type": "subscription.invalid",
  "code": "invalid_topic",
  "message": "One or more requested topics are not supported.",
  "recoverable": true,
  "supported_topics": ["signals", "trace", "market"]
}
```

Invalid generic subscriptions return an error envelope and close the socket with a policy-validation close code.

## WebSocket vs Webhook usage

Use WebSockets for live dashboards and operator monitoring where a connected client should receive immediate in-process updates. Use webhooks when an external system needs durable signed HTTP notifications, retries, and delivery logs. Both surfaces consume the same event backbone and must not bypass the Event Outbox.

## Reconnect guidance

Clients should reconnect with exponential backoff and treat missing heartbeats as a stale connection. `last_event_id` is accepted but replay is not available in this build, so clients should refresh state from REST APIs after reconnecting.

## Safety and security

WebSocket events are infrastructure notifications only. They are not legal verification, financial advice, Bitcoin consensus proof, payment approval, or authorization to execute transactions.

Payload serialization redacts sensitive material such as seed phrases, private keys, wallet files, xprv/yprv/zprv values, signing material, webhook secrets, authorization headers, bearer tokens, and API keys. If redaction occurs, the envelope includes:

```json
{
  "metadata": {
    "redacted": true,
    "redaction_reason": "sensitive_material"
  }
}
```

The stream preserves explicit degraded, fallback, and stale flags so clients do not hide uncertain data states. Trace events remain advisory-only and are not legal verification or Bitcoin consensus proof. Treasury and wallet stream data is metadata/status only; no seed phrase, private key, wallet file, or signing material belongs in a WebSocket payload.

## Observability

The implementation adds bounded WebSocket metrics for active connections, total connections, messages sent, send failures, invalid subscriptions, and heartbeats. Metrics avoid high-cardinality labels such as connection IDs or target URLs.

## Limitations and future work

- The broker is in-memory and single-process in this build.
- Distributed fanout using Redis/pubsub or another coordination layer is future work.
- Historical replay with `last_event_id` is not available in this build.
- Production-grade WebSocket auth and rate limiting are future hardening tasks.
- WebSocket delivery does not replace the Event Outbox or webhook dispatcher.

## Python SDK helper

The developer-preview Python SDK includes `client.websocket.subscribe_events(topics=[...])` for the generic stream and `client.websocket.subscribe("signals")` style helpers for specialized streams. The SDK helpers preserve the same no-custody payload rules and do not add replay or distributed fanout beyond the backend capabilities documented here.
