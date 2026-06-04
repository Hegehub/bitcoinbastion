# Historical Similarity Engine

Bitcoin Bastion's Historical Similarity Engine turns isolated Market Time Machine events into reusable market memory. It follows the production flow:

```text
News -> Canonical Event -> Pattern Classification -> Historical Search -> Similarity Ranking -> Reaction Statistics -> Evidence Packet
```

## What the engine does

The engine answers four questions for an event:

1. **How similar was the historical analog?** Deterministic component scores compare pattern, BTC relevance, sentiment, direction, impact profile, reaction windows, source quality, and provider confidence.
2. **What happened afterward historically?** Historical examples expose 15m, 1h, 4h, and 24h BTC reaction fields when available.
3. **How reliable is the comparison?** Reports include confidence breakdowns, provider confidence, sample counts, and reaction statistics.
4. **What limitations exist?** Every response includes historical-reference and correlation-only warnings.

## Deterministic scoring

No external AI dependency or embedding service is required. The first production model is rules-based and weighted across:

- pattern match / event type match
- BTC relevance and market impact alignment
- sentiment match
- direction match / reaction direction match
- time-window match
- historical reaction similarity
- source quality and provider confidence

Embeddings are intentionally represented by `pattern_embeddings_placeholder` only, so future semantic search can be added without creating a runtime dependency today.

## Frontend-ready output

`GET /api/v1/intelligence/similarity/{event_id}` returns:

- `similarity_score`
- `matched_pattern`
- `historical_examples`
- `reaction_statistics`
- `confidence_breakdown`
- `narrative_tags`
- `limitations`

## Required safety language

Historical similarity is not a prediction. Responses expose:

- `historical_reference_only`
- `correlation_not_causation`
- `not_financial_advice`
- `evidence_based`
- `historical_sample_count_low`
- `pattern_confidence_low`
- `provider_diversity_low`
- `market_structure_changed`
