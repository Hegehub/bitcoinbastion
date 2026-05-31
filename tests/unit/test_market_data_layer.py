from datetime import UTC, datetime

from app.services.market_data.aggregation import aggregate_btc_prices
from app.services.market_data.provider_models import NormalizedBTCPricePoint


def test_aggregation_median_and_count() -> None:
    pts = [
        NormalizedBTCPricePoint("a", "BTCUSD", 100.0, datetime.now(UTC), 100, 0.8, "h1"),
        NormalizedBTCPricePoint("b", "BTCUSD", 101.0, datetime.now(UTC), 110, 0.8, "h2"),
        NormalizedBTCPricePoint("c", "BTCUSD", 99.0, datetime.now(UTC), 90, 0.8, "h3"),
    ]
    agg = aggregate_btc_prices(pts)
    assert agg.median_price == 100.0
    assert agg.provider_count == 3
    assert agg.aggregated_confidence > 0.5
