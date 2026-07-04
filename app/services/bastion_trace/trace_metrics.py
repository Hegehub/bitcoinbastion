from prometheus_client import Counter, Gauge

TRACE_REQUESTS = Counter(
    "bastion_trace_requests_total", "Trace requests", ["tier", "operation", "status"]
)
TRACE_REPORTS = Counter("bastion_trace_reports_total", "Trace reports", ["tier", "status"])
TRACE_SCORE_BAND = Counter("bastion_trace_score_band_total", "Trace score band", ["tier", "band"])
TRACE_LITE = Counter("bastion_trace_lite_checks_total", "Lite checks", ["status"])
TRACE_BATCH = Counter("bastion_trace_batch_checks_total", "Batch checks", ["status"])
TRACE_REVIEW = Counter("bastion_trace_review_items_total", "Review items", ["status"])
TRACE_WATCH = Counter("bastion_trace_watchtower_entries_total", "Watchtower entries", ["status"])
TRACE_WATCH_ALERT = Counter(
    "bastion_trace_watchtower_alerts_total", "Watchtower alerts", ["severity"]
)
TRACE_DISAGREE = Counter(
    "bastion_trace_provider_disagreement_total", "Provider disagreement", ["severity"]
)
TRACE_SOURCE_REFRESH = Counter(
    "bastion_trace_source_refresh_total", "Source refresh", ["source_type", "status"]
)
TRACE_SOURCE_REFRESH_FAIL = Counter(
    "bastion_trace_source_refresh_failures_total", "Source refresh failures", ["source_type"]
)
TRACE_CONF = Gauge("bastion_trace_confidence", "Trace confidence", ["tier"])
TRACE_EVIDENCE_INDEP = Gauge(
    "bastion_trace_evidence_independence", "Evidence independence", ["tier"]
)
TRACE_PRIVACY = Gauge("bastion_trace_privacy_exposure_score", "Privacy exposure", ["tier"])
TRACE_PROOF = Counter("bastion_trace_proof_packets_total", "Proof packets", ["tier", "status"])
TRACE_REPLAY = Counter("bastion_trace_replay_total", "Replay attempts", ["status"])
TRACE_RUNTIME = Counter(
    "bastion_trace_runtime_events_total", "Runtime events", ["event_type", "severity", "status"]
)
