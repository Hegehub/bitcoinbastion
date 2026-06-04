# Pattern Library

The Market Time Machine pattern library is seeded into `market_patterns` and provides reusable classifications for historical similarity.

## Required production seed patterns

- ETF_INFLOW_SHOCK
- ETF_OUTFLOW_SHOCK
- SEC_ENFORCEMENT
- REGULATORY_APPROVAL
- REGULATORY_DELAY
- FED_LIQUIDITY
- FED_TIGHTENING
- CPI_SURPRISE
- MACRO_RISK_ON
- MACRO_RISK_OFF
- EXCHANGE_HACK
- CUSTODY_FAILURE
- MINER_CAPITULATION
- MINER_ACCUMULATION
- LARGE_LIQUIDATION
- BITCOIN_CORE_RELEASE
- LIGHTNING_ADOPTION
- INSTITUTIONAL_TREASURY
- SELF_CUSTODY_NARRATIVE
- SECURITY_VULNERABILITY

## Pattern model

`market_patterns` includes `pattern_code`, `display_name`, `category`, `description`, `typical_sentiment`, `typical_direction`, `default_time_window`, active state, and timestamps.

## Occurrences and statistics

- `pattern_occurrences` records classified articles, events, impacts, candle attributions, signals, confidence, and classification reason.
- `historical_reaction_statistics` records sample counts, median moves, and positive/negative/neutral ratios.
- `historical_similarity_matches` records reference/candidate occurrence links and confidence components.
