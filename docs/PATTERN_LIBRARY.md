# Pattern Library

The Bastion Market Time Machine maintains a production pattern library so every new news event can be compared with prior events of the same market-memory type. The canonical production catalog is stored in `market_patterns`; the compatibility/scoring catalog is stored in `market_pattern_library`.

## Initial production patterns

The seeded production library includes:

- `ETF_INFLOW_SHOCK`
- `ETF_OUTFLOW_SHOCK`
- `SEC_ENFORCEMENT`
- `SEC_APPROVAL`
- `FED_LIQUIDITY_SHOCK`
- `RATE_CUT_SIGNAL`
- `RATE_HIKE_SIGNAL`
- `EXCHANGE_HACK`
- `CUSTODY_FAILURE`
- `PRIVATE_KEY_LEAK`
- `MINER_CAPITULATION`
- `MINER_ACCUMULATION`
- `HALVING_NARRATIVE`
- `LIGHTNING_ADOPTION`
- `BITCOIN_CORE_RELEASE`
- `TREASURY_ADOPTION`
- `INSTITUTIONAL_ACCUMULATION`
- `MACRO_RISK_ON`
- `MACRO_RISK_OFF`
- `LIQUIDATION_CASCADE`
- `VOLATILITY_EXPANSION`

## Model fields

`market_patterns` stores `pattern_code`, `name`, `category`, `description`, `default_sentiment`, `default_impact_window`, `risk_profile`, `confidence_rules_json`, `is_active`, and timestamps. Existing `slug`, `expected_sentiment`, `expected_direction`, and `typical_impact_window` fields remain for backwards-compatible services.

## Safety posture

Pattern matches are historical context only. They are not predictions, do not establish causation, and must never be presented as trading instructions.
