from prometheus_client import Counter, Histogram

HISTORICAL_SIMILARITY_RUNS_TOTAL = Counter(
    "historical_similarity_runs_total", "Total historical similarity report runs."
)
HISTORICAL_SIMILARITY_FAILURES_TOTAL = Counter(
    "historical_similarity_failures_total", "Total failed historical similarity report runs."
)
PATTERN_CLASSIFICATIONS_TOTAL = Counter(
    "pattern_classifications_total", "Total market pattern classifications."
)
PATTERN_CLASSIFICATION_FAILURES_TOTAL = Counter(
    "pattern_classification_failures_total", "Total failed market pattern classifications."
)

HISTORICAL_SIMILARITY_REQUESTS_TOTAL = Counter(
    "historical_similarity_requests_total", "Total historical similarity API/service requests."
)
HISTORICAL_SIMILARITY_DURATION_SECONDS = Histogram(
    "historical_similarity_duration_seconds",
    "Historical similarity generation duration in seconds.",
)
HISTORICAL_SIMILARITY_CACHE_HITS = Counter(
    "historical_similarity_cache_hits", "Historical similarity cache hits."
)
PATTERN_MATCH_COUNT = Counter("pattern_match_count", "Pattern matcher candidates emitted.")
SIMILARITY_GENERATION_FAILURES = Counter(
    "similarity_generation_failures", "Failed historical similarity generations."
)

SIMILARITY_CALCULATIONS_TOTAL = Counter(
    "similarity_calculations_total", "Total BMTM historical similarity calculations."
)
HISTORICAL_PROFILES_GENERATED_TOTAL = Counter(
    "historical_profiles_generated_total", "Total historical reaction profiles generated."
)
CONFIDENCE_CALIBRATIONS_TOTAL = Counter(
    "confidence_calibrations_total", "Total historical confidence calibrations."
)
SIMILARITY_FAILURES_TOTAL = Counter(
    "similarity_failures_total", "Total BMTM historical similarity calculation failures."
)

SIMILARITY_REQUESTS_TOTAL = Counter(
    "similarity_requests_total", "Total historical similarity foundation requests."
)
SIMILARITY_GENERATION_DURATION_SECONDS = Histogram(
    "similarity_generation_duration_seconds",
    "Historical similarity foundation generation duration in seconds.",
)
SIMILARITY_MATCHES_FOUND = Counter(
    "similarity_matches_found", "Total historical similarity matches returned."
)

HISTORICAL_SIMILARITY_MATCHES_TOTAL = Counter(
    "historical_similarity_matches_total", "Total historical similarity matches returned."
)
MARKET_PATTERNS_TOTAL = Counter(
    "market_patterns_total", "Total market pattern rows ensured."
)
PATTERN_OCCURRENCES_TOTAL = Counter(
    "pattern_occurrences_total", "Total pattern occurrences recorded."
)
PATTERN_CONFIDENCE_CALCULATIONS_TOTAL = Counter(
    "pattern_confidence_calculations_total", "Total pattern confidence calculations."
)
