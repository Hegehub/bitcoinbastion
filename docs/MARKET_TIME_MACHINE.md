# Market Time Machine

Market Time Machine stores replayable market and intelligence context for BTC candles, news, source health, provider confidence, scoring, impact windows, and candle attribution.

## Candle attribution

Candle attribution ranks nearby news events for a BTC candle using time distance, BTC relevance, market-impact scoring, source confidence, provider confidence, and direction matching. It does not claim that an event caused a candle. All attribution output must preserve the limitation: **Correlation is not proof of causation.**

## News impact windows

Market Time Machine now persists article/event impact windows for 15m, 1h, 4h, and 24h after publication. Impact records store provider confidence, degraded-state limitations, confidence breakdowns, and window snapshots. The engine measures correlated BTC movement only; it does not claim causation.

## Production Candle Attribution

The Market Time Machine now stores candle attribution candidates, ranked attributions, and replayable context snapshots. Candidate search is timeframe-aware, ranking weights are configurable, and every attribution carries provider-health evidence and a no-causation limitation.
