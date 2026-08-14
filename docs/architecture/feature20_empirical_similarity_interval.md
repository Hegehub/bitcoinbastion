# Feature 20 statistical authority: empirical similarity-score quantiles

## Decision

Feature 20 is canonically **Uncertainty ribbons and hatching**. Its interval is a
retrospective description of dispersion in persisted similarity scores, not a
confidence interval, credible interval, prediction interval, forecast, or future BTC
price range.

| Question | Canonical answer | Evidence |
|---|---|---|
| Quantity | Distribution of persisted `similarity_score` values for eligible historical candidate contexts associated with one reference event | `HistoricalEventSimilarity.similarity_score` is the backend-owned bounded comparison statistic |
| Sampling unit | One distinct candidate historical `NewsEvent` context | `similar_event_id` is the stable candidate identity |
| Reference cohort | Up to 500 eligible persisted matches visible in the request transaction, ordered by score/event time/row ID | `MarketSimilarityReadService` |
| Interval required? | Yes; Feature 20 explicitly names ribbons/hatching and requires backend DTO/view-model and accessible alternatives | canonical Feature register |
| Existing inferential model? | No | repository producer audit found no posterior, standard error, covariance, or resampling distribution |

`Feature20Estimand = empirical distribution of backend-owned similarity-score ratios
across distinct eligible historical candidate contexts for one reference event at the
request boundary.`

`Feature20SamplingUnit = one distinct candidate historical NewsEvent context.`

## Selected method: M3 empirical distribution authority

The backend calculates the Hyndman-Fan type-7 10th and 90th empirical quantiles. The
result type is `EMPIRICAL_QUANTILE_INTERVAL`, its unit is `SIMILARITY_RATIO`, and its
subject is `HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION`.

Method identity:

* ID: `EMPIRICAL_SIMILARITY_SCORE_QUANTILES`
* version: `empirical-similarity-quantiles.v1`
* lower quantile: `0.10`
* upper quantile: `0.90`
* minimum sample: five distinct candidate contexts

The quantiles are a deliberate new backend product policy. They contain 80% of the
bounded empirical cohort under type-7 interpolation; they do **not** promise 80%
frequentist coverage.

## Dependence and assumptions

Historical candidate contexts can overlap in time, provider inputs, and Market regime.
They are not asserted IID. An IID/bootstrap confidence interval was rejected for that
reason. The empirical interval makes no independence assumption and no population
inference, but it preserves `TEMPORAL_DEPENDENCE_NOT_MODELED` as a material limitation.

Also rejected:

* confidence ± constant: no statistical meaning;
* provider min/max: provider disagreement is a distinct semantic;
* historical min/max called a CI: incorrect interval taxonomy;
* prediction interval: no forecasting model exists;
* credible interval: no posterior model exists;
* parametric CI: no standard-error/covariance authority exists.

## Eligibility, boundary, and sufficiency

Eligible observations must have a unique positive candidate event ID and a finite score
in `[0, 1]`. The calculation reads only persisted rows visible in the request transaction
and is bounded to 500 candidates. It never queries observations after that request
boundary. Fewer than five candidates returns `INSUFFICIENT_DATA` with no lower/upper
values—never `[0, 0]`, NaN, or fabricated fallback bounds.

Historical Replay does not recompute this interval. Prompt-10 Replay captures currently
have no stored Feature-20 interval, so historical Replay honestly omits it. This prevents
today's expanded cohort from being presented as what Bastion knew at capture time.

## Limitations

* `DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL`
* `TEMPORAL_DEPENDENCE_NOT_MODELED`
* `RETROSPECTIVE_NOT_FORECAST`
* `LOW_SAMPLE_COUNT` when fewer than five eligible contexts exist

## Runtime policy and non-goals

The deterministic calculation is performed on demand in the backend read service. It is
bounded and inexpensive, so it is not persisted or cached. Future changes to quantiles,
eligibility, interpolation, or cohort bounds require a new method version. The frontend
may position and format the returned band, but must not calculate lower or upper values.
