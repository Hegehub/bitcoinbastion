# Candlestick Intelligence Dashboard

The Candlestick Intelligence Dashboard answers a specific question:

```text
One candle formed. What evidence-backed factors might be relevant?
```

It does not answer whether a factor caused the candle, and it never predicts future price.

## Dashboard Route

`GET /market` renders the main dashboard with:

- timeline navigation;
- BTC candlestick chart;
- deterministic news markers;
- context panel;
- evidence panel;
- historical similarity panel;
- narrative panel.

## Candle API Contracts

- `GET /api/v1/intelligence/candles/{candle_id}` returns the candle dashboard DTO.
- `GET /api/v1/intelligence/candles/{candle_id}/events` returns candidate news, macro, security, and narrative events.
- `GET /api/v1/intelligence/candles/{candle_id}/evidence` returns an evidence panel DTO.
- `GET /api/v1/intelligence/candles/{candle_id}/similar` returns historical similarity preview rows.

## Chart Marker Philosophy

Markers are deterministic DTOs. They are not browser-generated inference and they do not overlap duplicates from the same timestamp bucket and marker type.

Marker types:

- 🟢 positive
- 🔴 negative
- 🟡 uncertain
- ⚠ security shock
- 🏛 regulatory event
- 🏦 institutional / ETF
- ⛏ mining
- ⚡ Lightning / Bitcoin Core
- 📈 narrative spike

## Candle Click DTO

Candle clicks expose:

- open, high, low, close;
- volume;
- price change percentage;
- dominant direction;
- volatility score;
- provider confidence;
- candidate news events;
- candidate macro events;
- candidate security events;
- candidate narrative events;
- attribution confidence.

## Evidence Integration

Evidence panels expose:

- evidence summary;
- evidence sources;
- confidence breakdown;
- provider snapshot;
- source snapshot;
- replay status;
- integrity status;
- limitations;
- JSON and Markdown export links;
- relationship links.

## Historical Similarity and Narrative Panels

The dashboard displays historical similarity previews and narrative strength from backend DTOs. These panels are historical references only and must include limitations. Historical comparison is never a promise of repetition.

## Attribution Limitations

Every attribution panel must expose:

```text
Correlation is not proof of causation.
evidence_based
operator_reviewed
confidence_score
```

Missing evidence, degraded providers, low confidence, and unavailable replay states are shown explicitly.
