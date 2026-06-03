# Market Signal Governance

Market Signal Governance is the operator-controlled publication layer for the Bastion Market Time Machine. It turns impact, attribution, and replay evidence into candidate signals, evaluates those candidates through publishing policy, requires operator review by default, and records delivery logs and audit history.

## Signal lifecycle

```text
impact / attribution / replay evidence
        -> candidate signal
        -> publishing policy
        -> operator review
        -> approved / rejected / held / degraded
        -> publication queue
        -> Telegram/API/Web visibility
        -> delivery logs + audit trail
```

The system must not publish strong market claims automatically without evidence and policy. It may say an event coincided with BTC movement and may have contributed, but it must not claim direct causation.

## Candidate generation

`SignalCandidateService` can create candidates from high-confidence `NewsPriceImpact` rows, `CandleAttribution` rows, and high-confidence `NewsEvent` rows. MVP signal types are `news_market_impact`, `candle_attribution`, `delayed_reaction`, `false_signal`, `security_shock`, `regulatory_risk`, `macro_shock`, `narrative_spike`, and `news_shock_index`.

Security, regulatory, narrative-spike, and news-shock-index detector adapters are safe placeholders when upstream detector data is unavailable; they return no candidates and preserve the limitation that missing evidence requires review.

## Publishing policy gates

The default publishing policy requires BTC relevance >= 0.45, impact confidence >= 0.65, source confidence >= 0.60, provider confidence >= 0.60, and evidence references when available. Auto-publish is disabled by default. Security/regulatory shocks, false signals, provider degraded state, low confidence, and missing evidence require operator review.

## Operator review

Operators may approve, reject, hold, request more evidence, mark false positives, or record confidence overrides. Review records do not delete evidence and do not mutate source facts; confidence overrides are stored on the review record for audit.

## Delivery logs

`SignalDeliveryLogService` records `telegram`, `api`, `web`, and `internal` delivery outcomes without requiring Telegram to exist. Delivery failures sanitize secrets before storage.

## Safety requirements

Every public signal includes `correlation_not_causation = true`, `not_financial_advice = true`, `operator_reviewed`, and `evidence_based`. Prohibited market-claim wording such as guaranteed, will pump, will dump, caused by, and certain is sanitized from signal text.

## Remaining limitations

The publication queue is backend-ready but does not push to Telegram automatically. Detector adapters for narrative spikes and shock indexes remain placeholders until those upstream data products emit production events. Operator identity uses optional reviewer IDs until production RBAC is connected.

## Duplicate and evidence governance hardening

Publishing policy blocks duplicate candidates that reference the same signal type, source entity type, and source entity ID. Public evidence payloads distinguish primary evidence from contextual provider-confidence metadata, so `evidence_based` is false when a candidate only has policy metadata and no article/event/impact/attribution/replay reference.

## Metrics

Signal governance emits bounded-label metrics only: `intelligence_signal_candidates_total`, `intelligence_signal_published_total`, `intelligence_signal_rejected_total`, `intelligence_signal_pending_review_total`, `intelligence_operator_reviews_total`, `intelligence_policy_blocks_total`, and `intelligence_signal_delivery_failures_total`.
