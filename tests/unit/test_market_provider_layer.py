from datetime import UTC, datetime

from app.services.market.aggregation import MarketMedianAggregationService
from app.services.market.confidence import provider_confidence
from app.services.market.schemas import ProviderPrice


def test_median_aggregation_and_degraded_mode() -> None:
    svc = MarketMedianAggregationService()
    result = svc.aggregate(
        [
            ProviderPrice("a", "BTCUSD", 100.0, datetime.now(UTC), 100, {}),
            ProviderPrice("b", "BTCUSD", 101.0, datetime.now(UTC), 110, {}),
            ProviderPrice("c", "BTCUSD", 99.0, datetime.now(UTC), 90, {}),
        ]
    )
    assert result.median_price_usd == 100.0
    assert result.provider_count == 3
    assert result.is_degraded is False


def test_confidence_degrades_on_failures() -> None:
    high = provider_confidence(50, 0, 0, 200)
    low = provider_confidence(2, 20, 5, 9000)
    assert low < high
