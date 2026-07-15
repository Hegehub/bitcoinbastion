# Candle Attribution Engine

The Candle Attribution Engine provides retrospective, evidence-first context for BTC candles. It answers which nearby news events may have been relevant to a specific candle without claiming direct causation.

## Philosophy

- Bitcoin-first and market-context focused.
- Correlation-oriented, not predictive.
- Operator-auditable through persisted attribution rows and replay logs.
- Confidence is capped to avoid fake certainty.
- Every response includes limitations, including: **Correlation is not proof of causation.**

## Candidate discovery

For each BTC candle the engine searches for `news_events` inside the candle interval, before the candle, and shortly after it. Defaults are configurable with:

- `ATTRIBUTION_WINDOW_BEFORE_MINUTES`
- `ATTRIBUTION_WINDOW_AFTER_MINUTES`
- `ATTRIBUTION_TOP_CANDIDATES`
- `ATTRIBUTION_MAX_CONFIDENCE`
- `ATTRIBUTION_ENABLE_REPLAY`

Timeframe-specific windows can also be supplied through
`ATTRIBUTION_WINDOW_CONFIG_JSON`. The current documented defaults are:

- `15m`: 45 minutes before and 15 minutes after;
- `1h`: 4 hours before and 1 hour after;
- `4h`: 12 hours before and 4 hours after;
- `1d`: 48 hours before and 12 hours after.

## Scoring

Candidate confidence combines event confidence, BTC relevance, market impact score, source confidence, provider confidence, time-distance weight, and sentiment/candle direction match. The score is clamped to `0.0` through the configured maximum confidence, defaulting to `0.92`.

Ranking weights can be overridden with `ATTRIBUTION_RANKING_WEIGHTS_JSON`.
The ranked factors include BTC relevance, market impact, source credibility,
news-impact confidence, historical-pattern support, provider confidence,
freshness, direction/sentiment match, and volatility. Multiple candidates may
be retained; the engine does not force a single cause.

## Replay support

Each run can persist an `attribution_replay_logs` entry containing the engine version, input hash, candidate count, search windows, ranking snapshot, and explanation snapshot. Replay logs support auditability and future evidence replay workflows.

## API

- `GET /api/v1/intelligence/candles/{candle_id}/attribution`
- `GET /api/v1/intelligence/candles/{candle_id}/top-events`
- `GET /api/v1/intelligence/candles/{candle_id}/replay`

These endpoints are designed for future UI aggregation such as “why did BTC move during this candle?” while preserving uncertainty and avoiding financial advice.

## Foundation context snapshots

The attribution foundation stores `candle_context_snapshots` for each attributed candle. These snapshots include volatility level, volume level, provider confidence, market regime, news/event density, positive/negative balance, macro/security/regulatory/institutional event counts, and a summary JSON payload for evidence drawers.

## BMTM-029 Ranking Layer

The production ranking layer in `app/services/intelligence/candle_attribution_ranking.py` focuses on the NewsEvent → BTC Candle relationship and produces ranked candidates for a candle. It searches:

- events in the 15m, 30m, 60m, and 4h windows before the candle;
- events published inside the candle interval;
- events up to 15m after the candle for delayed attribution analysis.

The service stores the final `rank`, score, explanation, limitations, time distance, direction match, and factor evidence in `candle_attributions`.

## Ranking model

The score is evidence-weighted rather than causal. The base formula multiplies:

`time_proximity × btc_relevance × market_impact × direction_match × provider_confidence`

It is then adjusted by historical pattern support, source health confidence, and event confidence. The response and persisted row include factor scores and weighted factor contributions so operators can see why an event ranked where it did.

## Direction matching

Direction match values are:

- `strong_match` — positive event with green candle, or negative event with red candle;
- `weak_match` — directional evidence exists but is not decisive;
- `neutral` — neutral/unknown event sentiment or flat candle;
- `contradictory` — event sentiment conflicts with candle direction.

Contradictory evidence reduces confidence but never forces the score to zero, because markets can react irrationally or to overlapping events.

## Confidence and limitations

Confidence bands are `LOW`, `MEDIUM`, and `HIGH`; there is no critical/certain band. Every attribution includes:

- `Correlation-based attribution. Not proof of causation.`
- `Correlation is not proof of causation.`

Additional limitations are emitted for provider degradation, low source confidence, weak historical support, insufficient evidence, and contradictory direction evidence.

## Operator review

Attributions are not automatically published as certainty. Review paths support
approval, rejection, false-attribution marking, confidence downgrade, and
operator notes. Candidate selection, score contributions, provider health,
window configuration, direction logic, confidence adjustments, and limitations
remain available as replayable evidence.
