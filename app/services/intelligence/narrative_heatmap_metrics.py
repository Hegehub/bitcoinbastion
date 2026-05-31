from prometheus_client import Counter, Gauge

NARRATIVE_CLASSIFICATIONS_TOTAL = Counter(
    "narrative_classifications_total", "Total narrative classifications emitted."
)
NARRATIVE_SNAPSHOTS_TOTAL = Counter(
    "narrative_snapshots_total", "Total narrative heatmap snapshots generated."
)
NARRATIVE_ROTATIONS_TOTAL = Counter(
    "narrative_rotations_total", "Total narrative rotation events detected."
)
NARRATIVE_CONFIDENCE_AVG = Gauge(
    "narrative_confidence_avg", "Average confidence of the latest narrative heatmap snapshot batch."
)
