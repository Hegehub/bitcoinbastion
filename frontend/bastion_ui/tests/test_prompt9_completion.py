from datetime import datetime
from decimal import Decimal

from bastion_ui.domain.prompt9 import adapt_jobs, adapt_market_overview, adapt_market_signals
from bastion_ui.realtime.prompt9_fixtures import EMPTY_JOBS, EMPTY_SIGNALS, UNAVAILABLE_MARKET
from bastion_ui.route_lifecycle import transition_actions
from bastion_ui.topology import ROUTE_BY_ID
from bastion_ui.transport.generated_http import (
    JobsApiV1OperationsJobsGetSuccess,
    MarketCurrentOverviewSuccess,
    TopSignalsApiV1SignalsTopGetSuccess,
)

NOW = datetime.fromisoformat("2026-01-15T12:00:00+00:00")
NOW_TEXT = "2026-01-15T12:00:00Z"


def test_jobs_dto_projection_is_typed_private_and_empty_is_distinct() -> None:
    response = JobsApiV1OperationsJobsGetSuccess.model_validate(
        [
            {
                "job_name": "signals.publish",
                "health_state": "degraded",
                "success": False,
                "last_start_at": NOW,
                "last_finish_at": NOW,
                "duration_ms": 0,
                "failure_reason": "bounded operator-safe summary",
                "next_scheduled_at": None,
                "retry_count": 2,
                "worker_name": "internal-worker-not-projected",
            }
        ]
    )
    projected = adapt_jobs(response)
    assert projected.jobs[0].name == "signals.publish"
    assert projected.jobs[0].status == "degraded"
    assert projected.jobs[0].duration_ms == 0
    assert "worker" not in projected.jobs[0].model_dump()
    assert "traceback" not in projected.jobs[0].model_dump()
    assert EMPTY_JOBS.jobs == ()


def test_market_overview_preserves_decimal_null_source_and_limitations() -> None:
    response = MarketCurrentOverviewSuccess.model_validate(
        {
            "data": {
                "symbol": "BTC",
                "pair": "BTCUSD",
                "price_usd": "0.00000001",
                "observed_at": NOW,
                "provider_count": 2,
                "provider_confidence": "0.987654321",
                "source": "market-data-aggregation",
                "limitations": ["one provider unavailable"],
            }
        }
    )
    projected = adapt_market_overview(response)
    assert projected.price_usd == Decimal("0.00000001")
    assert projected.provider_confidence == Decimal("0.987654321")
    assert projected.limitations == ("one provider unavailable",)
    assert UNAVAILABLE_MARKET.price_usd is None


def test_signal_adapter_copies_backend_semantics_without_direction_derivation() -> None:
    response = TopSignalsApiV1SignalsTopGetSuccess.model_validate(
        {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": 7,
                        "signal_type": "news-impact",
                        "title": "Backend title",
                        "summary": "Analytical observation",
                        "severity": "medium",
                        "confidence": Decimal("0.731"),
                        "score": Decimal("-0.25"),
                        "is_published": True,
                        "created_at": NOW,
                        "freshness": {
                            "computed_at": NOW_TEXT,
                            "is_stale": False,
                            "stale_reason": None,
                            "ttl_seconds": 300,
                        },
                        "explainability": None,
                        "horizons": None,
                    }
                ],
                "total": 1,
                "limit": 25,
                "offset": 0,
            },
        }
    )
    projected = adapt_market_signals(response)
    item = projected.signals[0]
    assert item.backend_score == Decimal("-0.25")
    assert item.confidence == Decimal("0.731")
    assert "direction" not in item.model_fields
    assert "strength" not in item.model_fields
    assert EMPTY_SIGNALS.signals == ()


def test_routes_dependencies_and_transition_cleanup_are_canonical() -> None:
    assert ROUTE_BY_ID["operations.jobs"].http_operations[-1] == "jobs_api_v1_operations_jobs_get"
    assert ROUTE_BY_ID["market.home"].http_operations == ("market_current_overview",)
    assert ROUTE_BY_ID["market.signals"].http_operations == ("top_signals_api_v1_signals_top_get",)
    for route in ("operations.jobs", "market.home", "market.signals"):
        actions = transition_actions(None, route)
        assert actions.invalidate_http is True
        assert actions.disconnect_websocket is True


def test_fixture_times_are_fixed_and_provenance_is_demo() -> None:
    assert EMPTY_JOBS.provenance.observed_at == datetime.fromisoformat("2026-01-15T12:00:00+00:00")
    assert EMPTY_JOBS.provenance.state.value == "DEMO_FIXTURE"
