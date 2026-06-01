from __future__ import annotations

from datetime import UTC, datetime
from statistics import median

from app.services.market.schemas import BTCMarketContext, ProviderPrice


class MarketMedianAggregationService:
    def aggregate(self, points: list[ProviderPrice]) -> BTCMarketContext:
        valid = [p for p in points if p.price_usd > 0]
        if not valid:
            return BTCMarketContext(0.0, 0, 0.0, 0.0, [], True, "no_provider_available", datetime.now(UTC))
        m = float(median([p.price_usd for p in valid]))
        filtered = [p for p in valid if abs(p.price_usd - m) / m <= 0.025]
        used = filtered or valid
        prices = [p.price_usd for p in used]
        spread = ((max(prices) - min(prices)) / m) * 100 if m else 0.0
        count = len(used)
        conf = 0.4 if count == 1 else 0.7 if count == 2 else 0.9
        conf -= min(0.4, spread / 50)
        degraded = count <= 1 or spread > 2.5
        reason = "only_one_provider_available" if count <= 1 else "provider_spread_too_large" if spread > 2.5 else ""
        return BTCMarketContext(float(median(prices)), count, round(max(0.0, min(1.0, conf)), 4), round(spread, 4), [{"provider": p.provider, "price": p.price_usd, "latency_ms": p.latency_ms} for p in used], degraded, reason, datetime.now(UTC))
