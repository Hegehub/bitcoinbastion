# Wow Layer Migration Matrix

All components below are consumed by `/console/wow` directly or through its route composition. Primary ownership is exclusive; a secondary consumer is allowed only after extraction. Current copy/data must be treated as preview or unavailable until contract tests prove otherwise.

| Component file | Primary owner | Target view-model / operations | Tests and removal condition |
|---|---|---|---|
| `trace_radar.py`, `risk_heatmap.py`, `privacy_exposure_lens.py` | Trace | report graph/risk/privacy with advisory limitations | Trace contract + browser; migrated Prompt 21–25 |
| `evidence_chain_viewer.py`, `audit_replay_timeline.py` | Evidence | packet chain/replay/provenance | Evidence contract + keyboard alternative; Prompt 26–29 |
| `provider_trust_matrix.py`, `node_pulse.py`, `degraded_mode_banner.py` | Operations | provider/node freshness and degradation | Operations browser forced states; Prompt 14–15 |
| `market_intelligence_wall.py`, `historical_similarity_lens.py` | Market | status/signal/similarity provenance | Market contract + table alternative; Prompt 16–20 |
| `policy_simulator_preview.py` | Policy | simulation input/result, never execution | PoA/Human Intent denial tests; Prompt 37 |
| `sovereign_grid_map.py`, `sovereignty_score_panel.py`, `citadel_mode_panel.py` | Sovereignty/Privacy | topology/assessment with synthetic/unavailable marker | reduced-motion/text alternative; Prompt 42 |
| `api_contract_explorer.py` | Developer tools | allowlisted runtime operation catalog/results | safe explorer tests; Prompt 45 |

Copy must preserve Trace/Market limitations and never imply execution, custody or production readiness. `/console/wow` remains until every row has a typed view-model, actual source or explicit unavailable state, tests, at most one secondary consumer, navigation compatibility decision, and one-release redirect evidence if externally linked. Do not copy the existing cards into core screens.
