from prometheus_client import Counter, Gauge, Histogram

PROVIDER_REQUEST_LATENCY_MS = Histogram(
    "market_provider_request_latency_ms", "Provider request latency", ["provider"]
)
PROVIDER_FAILURES_TOTAL = Counter(
    "market_provider_failures_total", "Provider failures", ["provider"]
)
PROVIDER_CONFIDENCE = Gauge("market_provider_confidence", "Provider confidence", ["provider"])
DEGRADED_PROVIDERS = Gauge("market_degraded_providers", "Degraded providers")
SUCCESSFUL_COLLECTIONS = Counter(
    "market_successful_collections_total", "Successful market collections"
)
OUTLIER_REJECTIONS = Counter("market_outlier_rejections_total", "Outlier rejections", ["provider"])
