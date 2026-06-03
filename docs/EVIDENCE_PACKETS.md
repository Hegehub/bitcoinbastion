# Evidence Packets

Evidence Packets are the production evidence bundle for the Bastion Market Time Machine. They convert article, event, impact, attribution, signal, and publication facts into replayable packets that operators can inspect before relying on a market-intelligence output.

## Architecture

The packet chain is Bitcoin-first and evidence-first:

```text
News article
  ↓
News event
  ↓
Impact calculation
  ↓
Candle attribution
  ↓
Signal candidate
  ↓
Policy evaluation
  ↓
Operator review
  ↓
Publication
```

Every packet records the source entity, linked article/event/impact/attribution/signal identifiers where available, confidence scores, provider confidence, source confidence, integrity snapshot, timeline, relationships, and limitations.

## Packet contents

Each packet exposes frontend-ready fields:

- `timeline`
- `confidence_breakdown`
- `evidence_chain`
- `limitations`
- `integrity_status`
- `operator_review_status`
- `publication_status`

Artifacts are persisted for evidence summary, evidence sources, confidence breakdown, provider health snapshot, source health snapshot, replay references, limitations, and frontend DTO state.

## Confidence provenance

Confidence is not a hidden score. Evidence packets expose:

- source contribution;
- provider contribution;
- impact contribution;
- attribution contribution;
- policy adjustments;
- operator overrides;
- final confidence.

Operator confidence overrides are recorded as review evidence and do not silently mutate the underlying source facts.

## Limitations

All packets expose at least the following limitation flags:

- `correlation_not_causation`
- `provider_degraded`
- `low_source_diversity`
- `limited_market_data`
- `operator_override_used`
- `missing_external_confirmation`
- `historical_similarity_unavailable`
- `evidence_based`
- `replayable`
- `operator_reviewed`

Evidence packets are not trading recommendations, do not claim causation, and do not guarantee future market behavior.

## Export

Packet exports support JSON and Markdown. PDF export remains future work.
