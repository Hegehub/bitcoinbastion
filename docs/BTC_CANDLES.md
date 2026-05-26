# BTC CANDLES

The BTC Candle Engine builds deterministic OHLC candles from `btc_price_points`.

- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d.
- Source mode is explicit (single-provider, multi-provider, degraded, rebuilt).
- Candles include provider confidence and integrity score.
- Rebuild is deterministic for same inputs and calculation version.
- No fabricated candles when there are no valid price points.
