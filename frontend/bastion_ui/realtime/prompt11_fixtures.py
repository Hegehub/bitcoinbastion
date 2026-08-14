"""Deterministic Feature-59/60 Prompt-11 analytical laboratory fixtures."""

from datetime import UTC, datetime
from decimal import Decimal

from bastion_ui.transport.generated_http import MarketSimilarityReportSuccess


def similarity_interval_fixture(*, sufficient: bool = True) -> MarketSimilarityReportSuccess:
    uncertainty = {
        "sufficiency": "AVAILABLE" if sufficient else "INSUFFICIENT",
        "sample_count": 5 if sufficient else 4,
        "coverage_dimension_count": 4,
        "confidence_ratio": None,
        "limitations": ["DEMO_FIXTURE"],
        "interval": {
            "subject": "HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION",
            "lower": Decimal("0.54"),
            "upper": Decimal("0.845"),
            "unit": "SIMILARITY_RATIO",
            "interval_type": "EMPIRICAL_QUANTILE_INTERVAL",
            "lower_quantile": Decimal("0.10"),
            "upper_quantile": Decimal("0.90"),
            "method_id": "EMPIRICAL_SIMILARITY_SCORE_QUANTILES",
            "method_version": "empirical-similarity-quantiles.v1",
            "sample_count": 5,
            "cohort": "ELIGIBLE_PERSISTED_MATCHES_BOUNDED_500_AT_REQUEST_BOUNDARY",
            "limitations": ["DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL", "DEMO_FIXTURE"],
        }
        if sufficient
        else None,
    }
    return MarketSimilarityReportSuccess.model_validate(
        {
            "reference_event_id": 7001,
            "method": "WEIGHTED_EVENT_CONTEXT_V1",
            "method_version": "historical-event-similarity.v1",
            "results": [],
            "uncertainty": uncertainty,
            "generated_at": datetime(2026, 8, 12, 12, tzinfo=UTC),
            "provenance": "LIVE",
            "interpretation": "RETROSPECTIVE_COMPARISON_NOT_FORECAST",
        }
    )
