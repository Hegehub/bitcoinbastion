from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from bastion_ui.domain.prompt11 import adapt_similarity
from bastion_ui.realtime.prompt11_fixtures import similarity_interval_fixture
from bastion_ui.topology import path_for
from bastion_ui.transport.generated_http import MarketSimilarityReportSuccess


def _response() -> MarketSimilarityReportSuccess:
    return MarketSimilarityReportSuccess.model_validate(
        {
            "reference_event_id": 7,
            "method": "WEIGHTED_EVENT_CONTEXT_V1",
            "method_version": "historical-event-similarity.v1",
            "results": [
                {
                    "result_id": 9,
                    "rank": 1,
                    "reference_event_id": 7,
                    "candidate_event_id": 8,
                    "candidate_title": "Historical context",
                    "candidate_occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
                    "replay_event_id": 8,
                    "score_ratio": Decimal("0.75"),
                    "score_meaning": "HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE",
                    "method": "WEIGHTED_EVENT_CONTEXT_V1",
                    "method_version": "historical-event-similarity.v1",
                    "dimensions": [
                        {"dimension": "PATTERN", "score_ratio": Decimal("0.8")}
                    ],
                    "limitations": ["Historical similarity is not a prediction."],
                }
            ],
            "uncertainty": {
                "sufficiency": "AVAILABLE",
                "sample_count": 1,
                "coverage_dimension_count": 4,
                "confidence_ratio": None,
                "limitations": ["Small sample."],
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
                    "limitations": ["DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL"],
                },
            },
            "generated_at": datetime(2026, 1, 1, tzinfo=UTC),
            "provenance": "LIVE",
            "interpretation": "RETROSPECTIVE_COMPARISON_NOT_FORECAST",
        }
    )


def test_similarity_adapter_preserves_backend_semantics() -> None:
    view = adapt_similarity(_response())
    assert view.results[0].rank == 1
    assert view.results[0].score_ratio == 0.75
    assert view.results[0].replay_event_id == 8
    assert view.confidence_ratio is None
    assert view.sufficiency == "AVAILABLE"
    assert view.interpretation == "RETROSPECTIVE_COMPARISON_NOT_FORECAST"
    assert view.interval is not None
    assert view.interval.lower == Decimal("0.54")
    assert view.interval.upper == Decimal("0.845")


def test_prompt11_route_is_canonical() -> None:
    assert path_for("market.similarity") == "/market/similarity"


def test_feature60_interval_fixtures_are_typed_and_explicit_demo() -> None:
    available = similarity_interval_fixture()
    unavailable = similarity_interval_fixture(sufficient=False)
    assert available.root.uncertainty.interval is not None
    assert "DEMO_FIXTURE" in available.root.uncertainty.interval.limitations
    assert unavailable.root.uncertainty.interval is None


def test_prediction_boundary_and_no_frontend_calculation() -> None:
    root = Path(__file__).parents[1]
    source = (root / "domain/prompt11.py").read_text() + (
        root / "components/prompt11_screens.py"
    ).read_text()
    assert "calculate_similarity" not in source
    assert "numpy" not in source
    assert "statistics.quantiles" not in source
    assert "interval.upper - interval.lower" not in source
    assert "will likely" not in source
    assert "chance history repeats" not in source
    assert "Similarity does not predict future outcomes" in source
