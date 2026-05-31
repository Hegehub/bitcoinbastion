# Historical Similarity Engine

The Historical Similarity Engine answers: "What similar Bitcoin market events happened before, and how did BTC react historically?" It is an evidence-based comparison layer, not a prediction engine or financial-advice system.

## Inputs

The current implementation accepts a canonical `NewsEvent` ID and compares it with historical `NewsEvent` rows, associated `NewsPriceImpact` records, and pattern-classification evidence.

## Scoring Dimensions

The deterministic score ranges from `0.0` to `1.0` and combines:

- shared market pattern
- sentiment similarity
- BTC relevance similarity
- market impact similarity
- volatility context similarity
- market direction similarity
- source/provider profile similarity
- institutional, regulatory, security, and macro flags

Scores are persisted in `historical_event_similarities` with component evidence and replayable explanations.

## Historical Reaction Profile

For a pattern, Bastion computes median and average BTC reactions over 15m, 1h, 4h, and 24h windows from historical `NewsPriceImpact` rows. The profile is stored in `pattern_reaction_profiles` with sample size and calibrated confidence.

## Confidence Calibration

`HistoricalConfidenceCalibrator` adjusts confidence using historical sample size, reaction consistency, provider confidence, and provider disagreement. Small samples and degraded providers reduce confidence.

## Required Safety Language

Every report includes: "Historical similarity does not guarantee future market behavior." Reports also state that correlation-based analysis is not proof of causation.

## Foundation API and Tables

The production foundation adds `historical_patterns`, `historical_similarity_matches`, and `historical_reaction_profiles` as the evidence-first base layer. Similarity scoring is deterministic and uses these MVP weights:

- Pattern match: 30%
- Sentiment match: 20%
- BTC relevance proximity: 15%
- Impact-window similarity: 15%
- Market-reaction similarity: 10%
- Source/category similarity: 10%

`HistoricalReactionService` stores event-level 15m, 1h, 4h, and 24h reactions, maximum positive/negative excursions, volatility score, and confidence. `HistoricalSimilarityService` persists replayable match rows with component scores and explanation JSON.

Required disclaimer: "Historical similarity does not imply future performance. Correlation is not proof of causation."
