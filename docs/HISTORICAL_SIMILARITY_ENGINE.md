# Historical Similarity Engine

The Historical Similarity Engine turns isolated Market Time Machine events into
reusable market memory. It provides deterministic historical context, not a
prediction, trading recommendation, or proof of causation.

## Flow

```text
News -> Canonical Event -> Pattern Classification -> Historical Search
     -> Similarity Ranking -> Reaction Statistics -> Evidence Packet
```

## Similarity factors

Similarity scoring is weighted across pattern/event-type match, sentiment,
direction, BTC relevance, market-impact alignment, time-window overlap,
historical reaction similarity, and provider/source confidence.

The implementation is rules-based and deterministic. It does not require an
external embedding service. `pattern_embeddings_placeholder` preserves a
future extension point without creating a runtime dependency.

## Similarity bands

Frontend DTOs expose production bands:

- `VERY_HIGH`: `0.90+`
- `HIGH`: `0.75+`
- `MEDIUM`: `0.60+`
- `LOW`: `0.40+`
- `VERY_LOW`: below `0.40`

Legacy responses may also expose `Weak`, `Moderate`, `Strong`, and `Very Strong` for backward compatibility.

## Historical context report

Reports include `pattern_name`, `pattern_category`, `similarity_score`, `similarity_band`, `historical_matches`, `historical_median`, `historical_average`, `pattern_confidence`, `reaction_statistics`, and limitations.

`GET /api/v1/intelligence/similarity/{event_id}` exposes frontend-ready fields
including the matched pattern, historical examples, reaction statistics,
confidence breakdown, narrative tags, and limitations. Historical examples may
include 15-minute, 1-hour, 4-hour, and 24-hour BTC reaction fields when the
underlying evidence exists.

## Required limitations

Every production context includes: `historical_similarity_not_prediction`,
`sample_size_limited`, `market_regime_changed`, `provider_limitations`,
`correlation_not_causation`, `historical_context_only`, `not_prediction`, and
`evidence_based`.

Additional diagnostic flags include `historical_sample_count_low`,
`pattern_confidence_low`, and `provider_diversity_low`. These fields must remain
visible when evidence is sparse or market structure has changed.
