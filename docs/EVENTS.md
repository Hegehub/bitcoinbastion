# Bitcoin Bastion Events

Bitcoin Bastion events are stable, typed contracts for future Event Bus, Outbox, Webhook, WebSocket, SDK, CLI, MCP, and plugin integrations. This document defines the event language only. It does **not** introduce delivery infrastructure, database outbox rows, migrations, broadcast sockets, webhook dispatchers, SDK clients, CLI commands, MCP servers, or plugin execution.

The event layer keeps the project posture explicit:

- Bitcoin-first and self-hosted capable.
- No custody, transaction signing, seed, secret recovery, wallet file, or signing-material handling.
- Operator-controlled actions; treasury and policy events do not auto-execute value movement.
- Evidence-driven outputs with limitations visible.
- Trace semantics are advisory-only, not legal verification, and not Bitcoin consensus proof.
- Market and signal events are informational and not financial advice.
- Degraded, fallback, stale, and provider-disagreement states remain visible.

## Naming Convention

Canonical event names use:

```text
domain.entity.action
```

Rules:

- lowercase only;
- dot-separated;
- no spaces;
- no marketing labels;
- stable public contracts once released.

Examples include `signal.published`, `trace.report.created`, `provider.degraded`, and `market.candle.attributed`.

## Base Event Envelope

Every event envelope uses these fields:

| Field | Meaning |
| --- | --- |
| `event_id` | UUID string for the event instance. |
| `event_type` | Canonical event type. |
| `event_version` | Integer event schema version, default `1`. |
| `domain` | Canonical domain. |
| `source_module` | Module or service that produced the event. |
| `occurred_at` | Timezone-aware event timestamp. |
| `aggregate_type` | Optional aggregate type. |
| `aggregate_id` | Optional aggregate identifier. |
| `correlation_id` | Optional correlation identifier. |
| `causation_id` | Optional causing event or workflow identifier. |
| `actor_type` | `system`, `operator`, `api_client`, `worker`, or `unknown`. |
| `actor_id` | Optional actor identifier. |
| `visibility` | `internal`, `public`, or `restricted`. |
| `severity` | `info`, `warning`, or `critical`. |
| `payload` | Domain payload as `dict[str, object]`. |
| `limitations` | Human-readable limitations to preserve safety context. |
| `safety_flags` | Canonical safety flags for downstream consumers. |

## Event Domains

The canonical domains are:

```text
news
event
signal
onchain
trace
wallet
treasury
policy
market
observability
provider
evidence
system
```

## Event Catalog

| Event type | Domain | Visibility | Severity | Webhook | WebSocket | Audit | Public safe | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `evidence.packet.created` | `evidence` | `internal` | `info` | `true` | `false` | `true` | `false` | Evidence packet was created. |
| `evidence.replay.completed` | `evidence` | `internal` | `info` | `false` | `false` | `true` | `false` | Evidence replay completed. |
| `evidence.replay.failed` | `evidence` | `internal` | `warning` | `false` | `false` | `true` | `false` | Evidence replay failed. |
| `job.failed` | `observability` | `internal` | `warning` | `true` | `false` | `true` | `false` | Background job failed. |
| `market.candle.attributed` | `market` | `internal` | `info` | `false` | `true` | `true` | `false` | Market candle attribution was produced. |
| `market.candle.closed` | `market` | `internal` | `info` | `false` | `true` | `false` | `true` | Market candle closed. |
| `market.price_tick.observed` | `market` | `internal` | `info` | `false` | `true` | `false` | `true` | Market price tick was observed. |
| `market.regime.changed` | `market` | `internal` | `info` | `false` | `true` | `false` | `false` | Market regime classification changed. |
| `news.article.created` | `news` | `internal` | `info` | `false` | `false` | `false` | `false` | News article was ingested. |
| `news.article.scored` | `news` | `internal` | `info` | `false` | `false` | `false` | `false` | News article received an advisory score. |
| `news.event.created` | `event` | `internal` | `info` | `false` | `false` | `false` | `false` | News event cluster was created. |
| `news.event.high_impact` | `event` | `internal` | `warning` | `false` | `false` | `false` | `false` | News event crossed high-impact review threshold. |
| `onchain.fee_spike` | `onchain` | `internal` | `info` | `false` | `true` | `false` | `false` | Fee environment spike was observed. |
| `onchain.large_transfer` | `onchain` | `internal` | `info` | `false` | `true` | `false` | `false` | Large on-chain transfer was observed. |
| `onchain.mempool_pressure` | `onchain` | `internal` | `info` | `false` | `true` | `false` | `false` | Mempool pressure changed materially. |
| `onchain.watchlist_hit` | `onchain` | `internal` | `warning` | `false` | `false` | `true` | `false` | On-chain watchlist condition matched. |
| `pipeline.lag.high` | `observability` | `internal` | `warning` | `true` | `true` | `true` | `false` | Pipeline lag crossed high threshold. |
| `policy.evaluation.completed` | `policy` | `internal` | `info` | `false` | `false` | `true` | `false` | Policy evaluation completed. |
| `policy.execution.failed` | `policy` | `internal` | `warning` | `false` | `false` | `true` | `false` | Policy execution failed. |
| `policy.warning.created` | `policy` | `internal` | `warning` | `false` | `false` | `true` | `false` | Policy warning was created. |
| `provider.degraded` | `provider` | `internal` | `warning` | `true` | `true` | `true` | `true` | Provider entered degraded state. |
| `provider.recovered` | `provider` | `internal` | `info` | `true` | `true` | `true` | `true` | Provider recovered from degraded state. |
| `signal.created` | `signal` | `internal` | `info` | `false` | `false` | `false` | `false` | Signal candidate was created. |
| `signal.operator_review_required` | `signal` | `internal` | `warning` | `false` | `false` | `true` | `false` | Signal requires operator review. |
| `signal.published` | `signal` | `restricted` | `info` | `true` | `true` | `true` | `false` | Signal was published after governance checks. |
| `signal.suppressed` | `signal` | `internal` | `info` | `false` | `false` | `true` | `false` | Signal was suppressed by policy or operator control. |
| `system.degraded_mode.entered` | `system` | `internal` | `warning` | `true` | `true` | `true` | `true` | System entered degraded mode. |
| `system.degraded_mode.exited` | `system` | `internal` | `info` | `true` | `true` | `true` | `true` | System exited degraded mode. |
| `system.runtime_warning.created` | `system` | `internal` | `warning` | `true` | `true` | `true` | `false` | System runtime warning was created. |
| `trace.batch.completed` | `trace` | `internal` | `info` | `true` | `false` | `true` | `false` | Trace batch screening completed. |
| `trace.report.created` | `trace` | `internal` | `info` | `true` | `false` | `true` | `false` | Trace report was created. |
| `trace.risk_band.changed` | `trace` | `internal` | `warning` | `true` | `false` | `true` | `false` | Trace risk band changed. |
| `trace.source_disagreement.detected` | `trace` | `internal` | `warning` | `false` | `false` | `true` | `false` | Trace source disagreement was detected. |
| `trace.treasury_destination_check.created` | `trace` | `internal` | `info` | `true` | `false` | `true` | `false` | Trace treasury destination check was created. |
| `treasury.approval.required` | `treasury` | `internal` | `warning` | `false` | `false` | `true` | `false` | Treasury request requires approval. |
| `treasury.policy.failed` | `treasury` | `internal` | `warning` | `false` | `false` | `true` | `false` | Treasury policy check failed. |
| `treasury.request.approved` | `treasury` | `internal` | `info` | `false` | `false` | `true` | `false` | Treasury request was approved by operator workflow. |
| `treasury.request.created` | `treasury` | `internal` | `info` | `false` | `false` | `true` | `false` | Treasury request was created. |
| `treasury.request.rejected` | `treasury` | `internal` | `info` | `false` | `false` | `true` | `false` | Treasury request was rejected by operator workflow. |
| `wallet.health.generated` | `wallet` | `internal` | `info` | `false` | `false` | `true` | `false` | Wallet health report metadata was generated. |
| `wallet.privacy_risk.high` | `wallet` | `internal` | `warning` | `false` | `false` | `true` | `false` | Wallet privacy risk crossed high advisory threshold. |

## Safety Flags

Canonical safety flags are reusable by future delivery layers:

```text
advisory_only
not_financial_advice
not_legal_verification
not_bitcoin_consensus_proof
no_custody
public_data_only
operator_review_required
degraded_data_visible
provider_disagreement_visible
stale_data_visible
correlation_not_causation
historical_similarity_not_prediction
no_auto_execution
```

## Payload Safety Rules

Event payloads must not contain seed phrases, mnemonics, private keys, extended private keys, wallet files, keystore blobs, signing material, or secret recovery phrases. The local validator inspects nested mappings and sequences and raises `EventPayloadSafetyError` for obvious forbidden material.

Trace payloads must avoid verdict-like wording. Trace reports remain advisory-only; they are not legal verification and not Bitcoin consensus proof. Market, news, and signal payloads must not imply financial advice or price prediction certainty.

## Future Webhook and WebSocket Use

The registry includes explicit `webhook_allowed` and `websocket_allowed` metadata so later prompts can build delivery without guessing. Permission in the registry is not delivery implementation. Prompt 4 creates no outbox, dispatcher, queue, socket route, or webhook delivery process.

## Versioning and Compatibility

- `event_version` starts at `1`.
- Additive payload fields are preferred for compatible changes.
- Removing or renaming event types is a breaking contract change.
- New safety flags may be added when future consumers need finer-grained limitations.
- Public-safe status must be explicit per event and must not be inferred from the domain.

## Examples

### `signal.published`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000001",
  "event_type": "signal.published",
  "event_version": 1,
  "domain": "signal",
  "source_module": "signal_governance",
  "occurred_at": "2026-06-06T12:00:00Z",
  "aggregate_type": "signal",
  "aggregate_id": "123",
  "correlation_id": "signal-123",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "restricted",
  "severity": "info",
  "payload": {
    "signal_id": 123,
    "confidence_band": "moderate",
    "operator_reviewed": true
  },
  "limitations": [
    "Signal output is informational and not financial advice.",
    "Correlation is not proof of causation."
  ],
  "safety_flags": [
    "not_financial_advice",
    "correlation_not_causation",
    "operator_review_required"
  ]
}
```

### `trace.report.created`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000002",
  "event_type": "trace.report.created",
  "event_version": 1,
  "domain": "trace",
  "source_module": "bastion_trace",
  "occurred_at": "2026-06-06T12:05:00Z",
  "aggregate_type": "trace_report",
  "aggregate_id": "456",
  "correlation_id": "trace-456",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "restricted",
  "severity": "info",
  "payload": {
    "report_id": 456,
    "risk_band": "elevated",
    "confidence": 0.72
  },
  "limitations": [
    "Trace reports are advisory-only.",
    "Trace reports are not legal verification.",
    "Trace reports are not Bitcoin consensus proof."
  ],
  "safety_flags": [
    "advisory_only",
    "not_legal_verification",
    "not_bitcoin_consensus_proof",
    "no_custody",
    "public_data_only"
  ]
}
```

### `provider.degraded`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000003",
  "event_type": "provider.degraded",
  "event_version": 1,
  "domain": "provider",
  "source_module": "provider_health",
  "occurred_at": "2026-06-06T12:10:00Z",
  "aggregate_type": "provider",
  "aggregate_id": "btc-price-feed-a",
  "correlation_id": "provider-btc-price-feed-a",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "public",
  "severity": "warning",
  "payload": {
    "provider": "btc-price-feed-a",
    "reason": "latency_threshold_exceeded"
  },
  "limitations": [
    "Provider degradation is visible to downstream consumers.",
    "Fallback data may be stale until recovery is observed."
  ],
  "safety_flags": ["degraded_data_visible", "stale_data_visible"]
}
```

### `market.candle.attributed`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000004",
  "event_type": "market.candle.attributed",
  "event_version": 1,
  "domain": "market",
  "source_module": "market_time_machine",
  "occurred_at": "2026-06-06T12:15:00Z",
  "aggregate_type": "market_candle",
  "aggregate_id": "btc-usd-2026-06-06T12:00:00Z",
  "correlation_id": "market-candle-20260606-1200",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "internal",
  "severity": "info",
  "payload": {
    "asset": "BTC",
    "window": "1h",
    "attribution_count": 3
  },
  "limitations": [
    "Market attribution is informational and not financial advice.",
    "Historical similarity is not prediction."
  ],
  "safety_flags": [
    "not_financial_advice",
    "correlation_not_causation",
    "historical_similarity_not_prediction"
  ]
}
```

### `treasury.approval.required`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000005",
  "event_type": "treasury.approval.required",
  "event_version": 1,
  "domain": "treasury",
  "source_module": "treasury_policy",
  "occurred_at": "2026-06-06T12:20:00Z",
  "aggregate_type": "treasury_request",
  "aggregate_id": "789",
  "correlation_id": "treasury-789",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "internal",
  "severity": "warning",
  "payload": {
    "request_id": 789,
    "policy": "operator_review"
  },
  "limitations": [
    "Treasury events do not execute transactions.",
    "Operator review is required before any external workflow proceeds."
  ],
  "safety_flags": ["no_auto_execution", "operator_review_required"]
}
```

### `evidence.packet.created`

```json
{
  "event_id": "00000000-0000-0000-0000-000000000006",
  "event_type": "evidence.packet.created",
  "event_version": 1,
  "domain": "evidence",
  "source_module": "evidence_service",
  "occurred_at": "2026-06-06T12:25:00Z",
  "aggregate_type": "evidence_packet",
  "aggregate_id": "packet-123",
  "correlation_id": "evidence-packet-123",
  "causation_id": null,
  "actor_type": "system",
  "actor_id": null,
  "visibility": "internal",
  "severity": "info",
  "payload": {
    "packet_id": "packet-123",
    "reference_count": 5
  },
  "limitations": [
    "Evidence packets summarize application-level data.",
    "Evidence packets are not legal verification."
  ],
  "safety_flags": ["advisory_only"]
}
```

## Event Outbox Persistence

The Event Outbox is implemented as a durable internal foundation for recording canonical events before future delivery layers consume them. External webhook dispatch is not implemented in this task. WebSocket streaming is not implemented in this task. Delivery retries are prepared at the persistence layer through status, attempt, lock, and scheduling fields, but dispatcher execution comes later.

See `docs/EVENT_OUTBOX.md` for the table contract and lifecycle.

## Internal Event Bus

The internal Event Bus now provides `publish_event(...)` as the reusable publishing API for future domain integrations. It validates registered event types, safety-checks payloads and metadata, deterministically serializes payloads, computes payload hashes, handles local idempotency keys, and records pending rows in `event_outbox`. It does not perform webhook dispatch, WebSocket streaming, Telegram delivery, SDK delivery, MCP delivery, or plugin execution.

See `docs/EVENT_BUS.md` for publisher behavior, examples, and limitations.

## Domain Integration Baseline

Selected existing backend workflows now publish internal events into the Event Outbox through the shared publisher. Current wired domains include Signals, Trace, Treasury, Evidence/Replay, Provider Health, On-chain ingestion, Wallet health, Policy evaluation, News article ingestion, and Market candle attribution.

This is not an external delivery layer. Webhooks, WebSocket streams, Telegram delivery, SDK consumption, CLI commands, MCP connectors, and plugin execution remain future work. Domain events must remain no-custody, advisory where applicable, and free of secrets or sensitive wallet material.

Known gaps are tracked in [`EVENT_INTEGRATION_GAPS.md`](EVENT_INTEGRATION_GAPS.md). Gaps are documented rather than filled with artificial placeholder events.
