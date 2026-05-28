from prometheus_client import Counter, Gauge, Histogram

CANDLE_ATTRIBUTION_RUNS_TOTAL = Counter(
    "candle_attribution_runs_total", "Total candle attribution engine runs."
)
CANDLE_ATTRIBUTION_FAILURES_TOTAL = Counter(
    "candle_attribution_failures_total", "Total failed candle attribution runs."
)
CANDLE_ATTRIBUTION_CANDIDATES_TOTAL = Counter(
    "candle_attribution_candidates_total", "Total candle attribution candidates evaluated."
)
CANDLE_ATTRIBUTION_CONFIDENCE_AVG = Gauge(
    "candle_attribution_confidence_avg", "Latest average candle attribution confidence."
)
CANDLE_ATTRIBUTION_DURATION_SECONDS = Histogram(
    "candle_attribution_duration_seconds", "Candle attribution run duration."
)

CANDLES_PROCESSED_TOTAL = Counter(
    "candles_processed_total", "Total BTC candles processed by the production attribution engine."
)
ATTRIBUTION_CANDIDATES_TOTAL = Counter(
    "attribution_candidates_total", "Total production attribution candidates evaluated."
)
ATTRIBUTION_CONFIDENCE_AVG = Gauge(
    "attribution_confidence_avg", "Latest average production attribution confidence."
)
LOW_CONFIDENCE_ATTRIBUTIONS_TOTAL = Counter(
    "low_confidence_attributions_total", "Total attributions below the configured confidence threshold."
)
PROVIDER_DISAGREEMENT_TOTAL = Counter(
    "provider_disagreement_total", "Total attribution runs with provider disagreement limitations."
)
ATTRIBUTION_RUNTIME_MS = Histogram(
    "attribution_runtime_ms", "Production candle attribution runtime in milliseconds."
)
