# Narrative Heatmap Engine

The Narrative Heatmap Engine identifies which Bitcoin market narratives are currently dominating discussion. It is narrative intelligence, not a sentiment-only or prediction system.

## Stored data

- `market_narratives`: active Bitcoin narrative catalog.
- `narrative_keywords`: deterministic keyword rules and weights per narrative.
- `narrative_snapshots`: per-window mention counts, weighted scores, sentiment, impact, source/event counts, provider confidence, trend direction, confidence, evidence, and limitations.

## Initial narratives

ETF, Institutional Adoption, Treasury Adoption, Mining, Bitcoin Core, Lightning, Macro Liquidity, Fed, Inflation, Dollar Strength, Regulation, SEC, Self Custody, Sovereignty, Exchange Risk, Security Incidents, Liquidations, and Market Structure.

## Scoring

Narrative scoring combines keyword score, news impact, BTC relevance, event/article confidence, source credibility, source count, freshness, and provider confidence. The output is a relative attention/importance score for the selected window.

## Trend states

The trend service deterministically classifies score movement as `RISING`, `FALLING`, `STABLE`, `SPIKING`, or `COOLING` by comparing the current snapshot with the previous snapshot for the same narrative.

## Dominance and rotation

The Narrative Dominance Index is each narrative's share of total weighted narrative score in the snapshot batch. Rotation detection compares consecutive dominance snapshots to identify when attention may be moving from one narrative to another.

## Evidence and limitations

Snapshots include top articles, top events, top keywords, provider state, confidence reasoning, and limitations. The engine must not claim narratives caused price moves. Use correlation-based language such as "may be associated" or "may contribute".
