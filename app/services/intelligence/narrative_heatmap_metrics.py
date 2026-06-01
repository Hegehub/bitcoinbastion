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

NARRATIVE_HEAT_UPDATES_TOTAL = Counter(
    "narrative_heat_updates_total", "Total narrative heatmap score update batches."
)
NARRATIVE_GROWTH_RECALCULATIONS_TOTAL = Counter(
    "narrative_growth_recalculations_total", "Total narrative growth score recalculations."
)
NARRATIVE_DOMINANCE_UPDATES_TOTAL = Counter(
    "narrative_dominance_updates_total", "Total narrative dominance index updates."
)
CLASSIFICATION_FAILURES_TOTAL = Counter(
    "classification_failures_total", "Total narrative classification failures."
)

NARRATIVES_DETECTED_TOTAL = Counter(
    "narratives_detected_total", "Total distinct narrative detections emitted by local classifier."
)
NARRATIVE_CLASSIFIER_FAILURES_TOTAL = Counter(
    "narrative_classifier_failures_total", "Total local narrative classifier failures."
)
