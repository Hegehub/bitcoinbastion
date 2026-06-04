# Narrative Memory

Narrative Memory tracks active Bitcoin market narratives and converts event clusters into normalized heat scores from `0.0` to `1.0`.

## Initial narratives

- ETF
- Macro
- Mining
- Lightning
- Bitcoin Core
- Institutional Adoption
- Self Custody
- Security
- Regulation
- Liquidity

## Heat calculation

The first production model is deterministic and combines:

- event count / volume
- weighted impact (`market_impact_score * btc_relevance_score`)
- source quality (`source_count` and provider confidence)
- market reaction magnitude
- time decay

Snapshots are persisted to `narrative_memory_snapshots` and exposed through `/api/v1/intelligence/narratives/active`, `/api/v1/intelligence/narratives/memory`, and `/api/v1/intelligence/narratives/history`.

## Safety boundaries

Narrative heat is historical context only. It must not be interpreted as a price forecast, causal proof, or financial advice.
