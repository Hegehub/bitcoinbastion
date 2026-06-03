from prometheus_client import Counter

INTELLIGENCE_SIGNAL_CANDIDATES_TOTAL = Counter(
    "intelligence_signal_candidates_total",
    "Total intelligence signal candidates created.",
    ["signal_type", "status"],
)
INTELLIGENCE_SIGNAL_PUBLISHED_TOTAL = Counter(
    "intelligence_signal_published_total",
    "Total intelligence signals published.",
    ["signal_type", "channel"],
)
INTELLIGENCE_SIGNAL_REJECTED_TOTAL = Counter(
    "intelligence_signal_rejected_total",
    "Total intelligence signals rejected.",
    ["signal_type", "reason_code"],
)
INTELLIGENCE_SIGNAL_PENDING_REVIEW_TOTAL = Counter(
    "intelligence_signal_pending_review_total",
    "Total intelligence signals requiring operator review.",
    ["signal_type", "reason_code"],
)
INTELLIGENCE_OPERATOR_REVIEWS_TOTAL = Counter(
    "intelligence_operator_reviews_total",
    "Total intelligence operator reviews recorded.",
    ["status"],
)
INTELLIGENCE_POLICY_BLOCKS_TOTAL = Counter(
    "intelligence_policy_blocks_total",
    "Total publishing policy blocks.",
    ["reason_code"],
)

# Backwards-compatible alias for older imports; canonical metric name is
# intelligence_policy_blocks_total per BMTM-P36.
INTELLIGENCE_PUBLISHING_POLICY_BLOCKS_TOTAL = INTELLIGENCE_POLICY_BLOCKS_TOTAL
INTELLIGENCE_SIGNAL_DELIVERY_FAILURES_TOTAL = Counter(
    "intelligence_signal_delivery_failures_total",
    "Total signal delivery failures.",
    ["channel", "reason_code"],
)
