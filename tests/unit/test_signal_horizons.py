from datetime import UTC, datetime
from app.db.models.signal import Signal
from app.schemas.signal import SignalOut
from app.services.horizons.signal_horizon_service import SignalHorizonService


def test_signal_horizon_service_returns_all_horizons() -> None:
    signal = Signal(
        signal_type="news",
        severity="high",
        score=0.82,
        confidence=0.77,
        title="ETF demand",
        summary="Demand increased",
    )

    horizons = SignalHorizonService().build(signal)

    assert set(horizons.keys()) == {"short", "medium", "long", "dominant"}


def test_signal_schema_extracts_horizons_from_explainability() -> None:
    signal = Signal(
        id=1,
        signal_type="news",
        severity="medium",
        score=0.5,
        confidence=0.6,
        title="Test",
        summary="Test",
        is_published=False,
        created_at=datetime.now(UTC),
        explainability_json='{"horizons": {"short": 0.4, "medium": 0.5, "long": 0.6, "dominant": "long"}}',
    )

    out = SignalOut.from_model_with_horizons(signal)

    assert out.horizons.get("dominant") == "long"
