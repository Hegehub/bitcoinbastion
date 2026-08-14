# Prompt 11 — Market analytics authority and accessibility matrix

## Prompt 11R two-blocker disposition

| Blocker | Existing authority | Exact missing evidence/semantic | Required repair | Acceptance proof |
|---|---|---|---|---|
| Authenticated Similarity browser flow | Prompt-9 ephemeral Ed25519 device/session bootstrap and persisted `historical_event_similarities` | Live protected request→DOM and Replay correlation | Reuse the single test-only bootstrap with `market:intelligence:read`; seed repository records | `run_prompt11r_browser.py` validates denial, PoP success, request counts, named DOM fields, Replay and narrow layout |
| Feature-20 statistical interval | Persisted score cohort and stable candidate identities | No prior interval policy | Adopt backend M3 type-7 empirical 10th/90th score quantiles | Typed response, live ribbon/text/table, known-input tests |

## Canonical feature ownership

| Feature | Canonical name | State | Consumer | Evidence |
|---|---|---|---|---|
| 18 | Historical similarity overlays | Implemented | `/market/similarity` | Typed persisted-score request → DTO → adapter → State → ranked DOM |
| 20 | Uncertainty ribbons and hatching | Implemented | Similarity empirical dispersion block | Backend empirical quantile interval, hatched ribbon, text and table alternative |
| 47 | Accessible chart/table alternative | Implemented | Similarity analytical table | Keyboard disclosure and named table columns mirror the typed result window |

## Authority matrix

| Concept | Backend owner | Contract semantics | Frontend role | Safe |
|---|---|---|---|---|
| score | `historical_event_similarities.similarity_score` | ratio `[0,1]`; higher means more similar, not predictive | decimal formatting | yes |
| rank | `MarketSimilarityReadService` | score descending, event time descending, row ID ascending | preserve | yes |
| method | historical similarity engine | `WEIGHTED_EVENT_CONTEXT_V1` / `historical-event-similarity.v1` | label | yes |
| dimensions | persisted pattern/sentiment/impact/volatility fields | bounded comparison ratios | table/list | yes |
| uncertainty support | read service | availability, result sample count, dimension-field coverage; confidence absent | textual display | yes |
| interval | empirical interval core | Type-7 empirical 10th/90th score quantiles; descriptive, not confidence/forecast | plot/format only | yes |
| export | none for Feature 47 | Feature 47 canonically requires a table alternative, not file export | not applicable | no |

## Prediction boundary

| Similarity concept | Permitted statement | Forbidden inference |
|---|---|---|
| score | This context is more similar under the named method. | The historical outcome will repeat. |
| rank | Backend ranked this candidate first. | The candidate is a forecast. |
| dimensions | These backend comparison dimensions aligned. | Alignment caused a market outcome. |
| sample count | This many persisted comparisons were returned. | Sample count is probability/confidence. |

## Chart and accessible-data inventory

| Chart ID | Screen | Authority | Accessible alternative | Missing-data policy | Motion/mobile |
|---|---|---|---|---|---|
| P11-SIM-RANK | Similarity | typed score/rank results | bounded table with rank, title, ratio and time | absent results remain empty/unavailable; no interpolation | no animation; responsive flow |

Feature 20 now uses the backend M3 policy documented in
`docs/architecture/feature20_empirical_similarity_interval.md`. A ribbon is rendered
only when at least five eligible contexts produce a typed interval.

## Statistical producer inventory and U3 decision

| Candidate | Classification | Reason |
|---|---|---|
| `HistoricalEventSimilarity` score/components | AUTHORITATIVE_RAW_STATISTICAL_INPUT | Persisted bounded comparison ratios, but no sampling distribution or interval method |
| `HistoricalConfidenceCalibrator` | CONFIDENCE_ONLY | Scalar calibration is not an interval and cannot define lower/upper |
| reaction summaries (`mean`, `median`, positive/negative ratio) | SUPPORT/SUFFICIENCY_ONLY | Descriptive statistics have no interval estimator, level, or unit contract |
| provider confidence/disagreement | PROVIDER_DISAGREEMENT_ONLY | Provider metadata cannot be repurposed as statistical bounds |
| Prometheus `Histogram` metrics | NOT_APPLICABLE | Operational telemetry, not per-result analytical uncertainty authority |
| tests/fixtures | TEST_ONLY | Cannot establish production analytical policy |

Selected case after Prompt 11R2 authority work: **M3 — the bounded empirical distribution
is itself the authority.** The backend reports an `EMPIRICAL_QUANTILE_INTERVAL` over
persisted similarity ratios. It makes no coverage, IID, causal, or forecasting claim.

## Invariants

* `frontend_similarity_calculation_count = 0`
* `frontend_similarity_to_prediction_inference_count = 0`
* `frontend_uncertainty_calculation_count = 0`
* `frontend_market_conclusion_recomputations = 0`
* Export is `NOT_APPLICABLE`: canonical Feature 47 is the accessible table alternative.
