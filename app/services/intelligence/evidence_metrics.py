from prometheus_client import Counter

EVIDENCE_PACKETS_GENERATED_TOTAL = Counter(
    "evidence_packets_generated_total",
    "Total evidence packets generated.",
    ["packet_type"],
)
EVIDENCE_REPLAY_REQUESTS_TOTAL = Counter(
    "evidence_replay_requests_total",
    "Total evidence replay requests.",
    ["entity_type"],
)
EVIDENCE_REPLAY_FAILURES_TOTAL = Counter(
    "evidence_replay_failures_total",
    "Total evidence replay failures.",
    ["entity_type", "reason_code"],
)
EVIDENCE_INTEGRITY_CHECKS_TOTAL = Counter(
    "evidence_integrity_checks_total",
    "Total evidence integrity checks.",
    ["entity_type", "status"],
)
EVIDENCE_INTEGRITY_MISMATCHES_TOTAL = Counter(
    "evidence_integrity_mismatches_total",
    "Total evidence integrity mismatches.",
    ["entity_type"],
)
