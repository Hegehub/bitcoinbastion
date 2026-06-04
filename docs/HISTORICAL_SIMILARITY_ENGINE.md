# Historical Similarity Engine

The Historical Similarity Engine adds long-term market memory to Bastion Market Time Machine.

## Flow

```text
News Event
  -> Pattern Classification
  -> Historical Search
  -> Similarity Scoring
  -> Reaction Analysis
  -> Evidence Packet
  -> Historical Report
```

## Similarity factors

Similarity scoring is weighted across pattern/event-type match, sentiment match, BTC relevance and market impact, time-window overlap, provider/source confidence, and reaction-profile similarity.

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

## Required limitations

Every production context includes: `historical_similarity_not_prediction`, `sample_size_limited`, `market_regime_changed`, `provider_limitations`, `correlation_not_causation`, `historical_context_only`, `not_prediction`, and `evidence_based`.
