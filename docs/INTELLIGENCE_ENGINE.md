# Intelligence Engine

Bitcoin Bastion intelligence services are Bitcoin-first, evidence-oriented, no-custody, and operator-controlled. They provide context, explainability, replay evidence, and limitations; they do not provide financial advice or guaranteed predictions.

## Historical Similarity Engine

The Historical Similarity Engine compares a NewsEvent, Candle Attribution, article-linked event, market signal, or narrative event against historical market-memory profiles. It produces historical analogs, reaction statistics, confidence, limitations, and evidence for operators.

### Pattern Library

The `market_pattern_library` table seeds deterministic patterns such as ETF inflow/outflow shocks, SEC enforcement, regulatory approvals/delays, Fed easing/tightening, exchange hacks, custody failures, miner capitulation/accumulation, liquidation cascades, Bitcoin Core releases, Lightning adoption, treasury adoption, institutional accumulation, macro risk-on/off, security incidents, and volatility expansion.

### Similarity Scoring

Similarity scoring is deterministic and explainable:

- Event type match: 25%
- Sentiment match: 15%
- Narrative match: 20%
- Impact-score similarity: 15%
- Price-reaction similarity: 15%
- Confidence similarity: 10%

Scores map to Weak, Moderate, Strong, and Very Strong bands. These bands are confidence context only, not future-performance claims.

### Limitations

Every report includes the limitations that correlation is not proof of causation, past reactions do not guarantee future market behavior, and historical similarity does not guarantee future outcomes.

## Narrative Heatmap Engine

The Intelligence Layer includes a deterministic Narrative Heatmap Engine. It stores `market_narratives`, `narrative_keywords`, and `narrative_snapshots`, classifies news articles/events into one or more narratives, scores each narrative window, detects `RISING`, `FALLING`, `STABLE`, `SPIKING`, and `COOLING` trend states, and emits timeline entries when a narrative enters a rising/spiking state.

The Narrative Dominance Index is the narrative's share of total weighted narrative score in a snapshot batch. Narrative Rotation detection compares consecutive dominance snapshots and reports when attention may be rotating from a falling narrative to a rising narrative. All outputs include limitations and must use correlation-based language only.
