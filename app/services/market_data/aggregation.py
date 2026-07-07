from __future__ import annotations

from datetime import UTC, datetime
from statistics import median

from app.services.market_data.provider_models import AggregatedBTCPrice, NormalizedBTCPricePoint


def aggregate_btc_prices(points: list[NormalizedBTCPricePoint]) -> AggregatedBTCPrice:
    valid = [p for p in points if p.price_usd > 0]
    if not valid:
        return AggregatedBTCPrice(0.0, 0, 0.0, 0.0, [], True, datetime.now(UTC))
    prices = [p.price_usd for p in valid]
    med = median(prices)
    filtered = [p for p in valid if abs(p.price_usd - med) / med <= 0.02]
    used = filtered or valid
    used_prices = [p.price_usd for p in used]
    spread = ((max(used_prices) - min(used_prices)) / med) * 100 if med else 0.0
    pc = len(used)
    conf = 0.35 if pc == 1 else 0.7 if pc == 2 else 0.9
    conf = max(0.0, min(1.0, conf - min(0.3, spread / 100)))
    return AggregatedBTCPrice(
        median_price=float(median(used_prices)),
        provider_count=pc,
        provider_spread_pct=round(spread, 4),
        aggregated_confidence=round(conf, 4),
        providers_used=[
            {"provider": p.provider, "price": p.price_usd, "confidence": p.provider_confidence}
            for p in used
        ],
        degraded_mode=pc < 2,
        generated_at=datetime.now(UTC),
    )
