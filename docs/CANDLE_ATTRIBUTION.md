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

## Scoring

Candidate confidence combines event confidence, BTC relevance, market impact score, source confidence, provider confidence, time-distance weight, and sentiment/candle direction match. The score is clamped to `0.0` through the configured maximum confidence, defaulting to `0.92`.

## Replay support

Each run can persist an `attribution_replay_logs` entry containing the engine version, input hash, candidate count, search windows, ranking snapshot, and explanation snapshot. Replay logs support auditability and future evidence replay workflows.

## API

- `GET /api/v1/intelligence/candles/{candle_id}/attribution`
- `GET /api/v1/intelligence/candles/{candle_id}/top-events`
- `GET /api/v1/intelligence/candles/{candle_id}/replay`

These endpoints are designed for future UI aggregation such as “why did BTC move during this candle?” while preserving uncertainty and avoiding financial advice.
