# Candle Attribution Engine

The production Candle Attribution Engine estimates which news/events/signals **may have contributed** to a BTC candle. It is retrospective market context, not prediction, trading advice, or proof of causation.

## Safety guarantee

Every attribution includes the limitation: **Correlation is not proof of causation.** Explanations use uncertainty-aware language such as "may have contributed", "possibly", "correlated with", and "coincided with".

## Candidate windows

Candidate search windows are configurable through `ATTRIBUTION_WINDOW_CONFIG_JSON` and default to:

- `15m`: 45 minutes before, 15 minutes after
- `1h`: 4 hours before, 1 hour after
- `4h`: 12 hours before, 4 hours after
- `1d`: 48 hours before, 12 hours after

## Ranking features

Candidates are ranked with configurable weights from `ATTRIBUTION_RANKING_WEIGHTS_JSON`:

- BTC relevance
- market impact
- source credibility
- news impact confidence
- historical similarity placeholder
- pattern-library placeholder
- provider confidence
- time-decay freshness
- direction/sentiment match
- volatility weight

The engine supports multi-event attribution and persists the top configured candidates instead of forcing a single cause.

## Replayable evidence

Each attribution stores replayable evidence references including candidate selection, score contributions, provider health, configured time windows, ranking features, direction logic, confidence adjustments, and limitations.

## Operator review

Attributions are not auto-published as certainty. API review hooks support approval, rejection, false-attribution marking, confidence downgrade, and operator notes.
