from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.btc_price_points import BTCPricePoint
from app.db.models.market_provider_health import MarketProviderHealth
from app.services.market.aggregation import MarketMedianAggregationService
from app.services.market.health import update_provider_health
from app.services.market.providers.binance import BinanceProvider
from app.services.market.providers.bitstamp import BitstampProvider
from app.services.market.providers.base import BaseMarketProvider
from app.services.market.providers.coinbase import CoinbaseProvider
from app.services.market.providers.kraken import KrakenProvider
from app.services.market.schemas import BTCMarketContext


def provider_registry() -> list[BaseMarketProvider]:
    return [BinanceProvider(), KrakenProvider(), CoinbaseProvider(), BitstampProvider()]


class BTCPriceCollector:
    def collect(self, db: Session) -> BTCMarketContext:
        points = []
        round_id = hashlib.sha256(str(db.execute(select(BTCPricePoint.id).order_by(BTCPricePoint.id.desc()).limit(1)).scalar() or 0).encode()).hexdigest()[:16]
        for provider in provider_registry():
            try:
                p = provider.fetch_btc_price()
                points.append(p)
                update_provider_health(db, p.provider, True, p.latency_ms, 200)
                db.add(BTCPricePoint(provider_name=p.provider, symbol="BTC", pair=p.pair, price_usd=p.price_usd, observed_at=p.observed_at, provider_confidence=0.8, provider_latency_ms=p.latency_ms, aggregation_round_id=round_id, is_median_selected=False, metadata_json={"raw_payload_hash": hashlib.sha256(json.dumps(p.raw_payload, sort_keys=True).encode()).hexdigest()}))
            except Exception as exc:
                update_provider_health(db, provider.provider_name(), False, None, None, str(exc))
        context = MarketMedianAggregationService().aggregate(points)
        if context.providers:
            selected = {x["provider"] for x in context.providers}
            rows = list(db.execute(select(BTCPricePoint).where(BTCPricePoint.aggregation_round_id == round_id)).scalars())
            for row in rows:
                row.is_median_selected = row.provider_name in selected
        db.commit()
        return context

    def providers_health(self, db: Session) -> list[MarketProviderHealth]:
        return list(db.execute(select(MarketProviderHealth).order_by(MarketProviderHealth.updated_at.desc())).scalars())
