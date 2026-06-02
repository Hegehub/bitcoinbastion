# Market Time Machine

Market Time Machine stores replayable market and intelligence context for BTC candles, news, source health, provider confidence, scoring, impact windows, and candle attribution.

## Candle attribution

Candle attribution ranks nearby news events for a BTC candle using time distance, BTC relevance, market-impact scoring, source confidence, provider confidence, and direction matching. It does not claim that an event caused a candle. All attribution output must preserve the limitation: **Correlation is not proof of causation.**

## News impact windows

Market Time Machine now persists article/event impact windows for 15m, 1h, 4h, and 24h after publication. Impact records store provider confidence, degraded-state limitations, confidence breakdowns, and window snapshots. The engine measures correlated BTC movement only; it does not claim causation.

## Production Candle Attribution

The Market Time Machine now stores candle attribution candidates, ranked attributions, and replayable context snapshots. Candidate search is timeframe-aware, ranking weights are configurable, and every attribution carries provider-health evidence and a no-causation limitation.

## Candle context snapshots

Candle attribution now writes `candle_context_snapshots` alongside ranked attributions and candidate rows so Market Time Machine views can show provider state, volatility/volume context, event density, and category pressure without making causation claims.

## Historical Similarity Engine

Market Time Machine now records normalized historical event profiles and correlation-only similarity results. The engine compares a new NewsEvent, Candle Attribution, or News Impact profile against historical patterns, narratives, sentiment, impact windows, provider confidence, and confidence profiles.

Historical similarity is evidence context, not a prediction system. Responses always include the limitations: **Correlation is not proof of causation.** Past reactions do not guarantee future market behavior.

Similarity evidence is also prepared for attribution evidence packets through `similar_historical_events` and `historical_similarity_summary`, so future UI panels can show pattern comparisons without implying causation.

## Production Historical Similarity Package

The production historical similarity package under `app/services/intelligence/historical_similarity/` separates scoring, pattern matching, explanation, and report orchestration. It supports NewsEvent, article, signal, and future candle/narrative-cluster adapters with UI-ready fields such as `top_similar_events`, `reaction_summary`, `reaction_distribution`, `pattern_name`, and confidence. It remains correlation-based analysis only and must not be used as a prediction engine.

## Historical Similarity Foundation

Market Time Machine now includes a foundation layer that compares a current Bitcoin market event against historical events using observable evidence only. It stores historical patterns, event reaction profiles, and replayable similarity matches. The MVP score is explainable: pattern, sentiment, BTC relevance, impact-window, reaction, and source/category similarity.

This is not a prediction engine. Historical similarity does not imply future performance. Correlation is not proof of causation.

## Narrative Heatmap Engine

Market Time Machine now includes a backend Narrative Heatmap Engine for identifying which Bitcoin narratives are dominating discussion over 1h, 4h, 24h, 7d, and 30d windows. It classifies NewsArticles and NewsEvents into deterministic narratives such as ETF, institutional adoption, treasury adoption, Lightning, Bitcoin Core, mining, macro liquidity, Fed, inflation, regulation, SEC, self-custody, sovereignty, exchange risk, security incidents, liquidations, and market structure.

Narrative scores combine keyword evidence, news impact, BTC relevance, event confidence, source credibility, source count, freshness, and provider confidence. The heatmap exposes top narratives, rising/falling narratives, highest-impact narratives, dominance share, trend states, evidence, and limitations. Narrative outputs are correlation-based; they may be associated with market context but do not prove causation or predict BTC price movement.

## BMTM-P35 Market Memory Engine

The Market Time Machine now has a production Market Memory package at `app/services/intelligence/market_memory/`. The package builds an `EventFingerprint` from Bitcoin relevance, market impact, sentiment, institutional/macro/regulatory/security context, source count, 15m/1h/4h/24h BTC reaction windows, direction, volatility profile, and provider confidence. The historical similarity facade ranks candidate events, persists reusable `market_memory_records`, creates replay payloads, and exposes market-memory evidence without making prediction or causality claims.

Replay output shows the event analyzed, candidate events, similarity scores, pattern assignments, reason codes, and final ranking. Operators can audit or override pattern confidence, approve/reject pattern assignments, add notes, and mark false similarities through auditable review records.

Safety requirements for Market Memory responses are: Historical similarity is not prediction. Correlation is not proof of causation. Past market reactions do not guarantee future outcomes. Do not generate trading recommendations.
