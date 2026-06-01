# News Impact Engine

The News Impact Engine measures how BTC price moved after a news article or canonical `NewsEvent` was published. It is correlation-based and evidence-first; it must never claim direct causation or provide trading advice.

## Windows

The production engine evaluates configurable windows through `NEWS_IMPACT_WINDOWS_MINUTES`, defaulting to `15,60,240,1440` for 15m, 1h, 4h, and 24h.

For each window the engine stores an `impact_window_snapshots` row with:

- price before / after,
- percent and absolute change,
- volatility score,
- provider confidence,
- direction match,
- degraded state.

## Price lookup

The engine prefers candle-aligned BTC prices from `btc_candles`. If a candle is unavailable it falls back to nearby raw `btc_price_points`, preferring median-selected points when available. Missing or low-provider data lowers confidence and records degraded limitations instead of fabricating prices.

## Confidence

`impact_confidence_score` combines Bitcoin relevance, source credibility, price-move strength, sentiment/direction match, provider confidence, freshness, and volatility adjustment. High-volatility conditions reduce confidence because attribution is noisier.

Confidence bands are `VERY_LOW`, `LOW`, `MEDIUM`, `HIGH`, and `VERY_HIGH`.

## Limitations

Every impact includes limitations. Required limitation keys include `correlation_not_causation`, and degraded cases may include `insufficient_price_data`, `low_provider_confidence`, `low_source_confidence`, `delayed_reaction`, `high_market_volatility`, and `incomplete_market_context`.
