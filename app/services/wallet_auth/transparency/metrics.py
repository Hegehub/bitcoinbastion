"""Low-cardinality transparency metrics; identifiers are deliberately not labels."""

from prometheus_client import Counter, Gauge

CHECKPOINTS_CREATED = Counter(
    "transparency_checkpoints_created_total", "Signed checkpoints created", ["checkpoint_type", "environment"]
)
CHECKPOINT_FAILURES = Counter(
    "transparency_checkpoint_failures_total", "Checkpoint lifecycle failures", ["checkpoint_type", "environment", "result"]
)
VERIFICATION_FAILURES = Counter(
    "transparency_verification_failures_total", "Checkpoint verification failures", ["checkpoint_type", "environment", "result"]
)
CHAIN_GAPS = Counter(
    "transparency_chain_gaps_total", "Detected checkpoint chain gaps", ["checkpoint_type", "environment"]
)
PUBLICATION_FAILURES = Counter(
    "transparency_publication_failures_total", "Checkpoint publication failures", ["checkpoint_type", "environment", "publication_target"]
)
MERKLE_PROOF_FAILURES = Counter(
    "transparency_merkle_proof_failures_total", "Merkle proof failures", ["checkpoint_type", "environment"]
)
PRIVACY_REJECTIONS = Counter(
    "transparency_privacy_rejections_total", "Rejected unsafe checkpoint sources", ["checkpoint_type", "environment"]
)
LATEST_SEQUENCE = Gauge(
    "transparency_latest_sequence", "Latest checkpoint sequence", ["checkpoint_type", "environment"]
)
CHECKPOINT_SOURCE_COUNT = Gauge(
    "transparency_checkpoint_source_count", "Sources in the latest checkpoint", ["checkpoint_type", "environment"]
)
