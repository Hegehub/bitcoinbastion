# Market Pattern Library

Bitcoin Bastion keeps a production market-pattern catalog for Market Time Machine evidence workflows. The catalog is Bitcoin-first and exists to classify historical context, not to predict future price movement.

## Model

`market_patterns` stores:

- `slug`, `name`, `category`, and `description`
- expected sentiment, expected direction, and typical impact window
- historical reaction profile metadata
- confidence rules used by historical-memory services
- active status and timestamps

## Seeded Patterns

The initial catalog contains ETF flow shocks, Fed liquidity regimes, SEC approval/enforcement events, Bitcoin protocol adoption, miner behavior, exchange/security failures, institutional and treasury adoption, macro risk regimes, liquidation cascades, halving narratives, self-custody waves, and sovereignty adoption.

## Pattern Classification

`PatternClassificationService` and `MarketMemoryService` can classify a `NewsEvent` into multiple ranked pattern candidates. Each classification includes:

- pattern slug and category
- classification confidence
- keyword/category/sentiment reasons
- persisted evidence in `event_pattern_matches`

## Limitations

- Pattern classification is deterministic and explainable; it is not a black-box model.
- Multiple patterns may apply to one event.
- Historical similarity does not guarantee future market behavior.
- Correlation-based analysis is not proof of causation.
