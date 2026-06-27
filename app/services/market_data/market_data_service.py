from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.btc_price_point import BTCPricePoint
from app.services.market.timeseries_repository import MarketTimeSeriesRepository
from app.services.market_data.aggregation import aggregate_btc_prices
from app.services.market_data.provider_health import record_provider_result
from app.services.market_data.metrics import (
    SUCCESSFUL_COLLECTIONS,
    PROVIDER_FAILURES_TOTAL,
    PROVIDER_CONFIDENCE,
)
from app.services.market_data.provider_registry import get_providers


class MarketDataService:
    def collect_btc_price(self, db: Session) -> dict[str, object]:
        points = []
        for provider in get_providers():
            try:
                p = provider.fetch_ticker()
                points.append(p)
                MarketTimeSeriesRepository(db).insert_price_point(
                    provider=p.provider,
                    pair=p.pair,
                    price_usd=p.price_usd,
                    observed_at=p.observed_at,
                    latency_ms=p.latency_ms,
                    provider_confidence=p.provider_confidence,
                    raw_payload_hash=p.raw_payload_hash,
                    metadata_json=p.metadata_json,
                )
                row = record_provider_result(db, p.provider, True, p.latency_ms, 200)
                PROVIDER_CONFIDENCE.labels(provider=p.provider).set(row.provider_confidence)
            except Exception as exc:
                row = record_provider_result(
                    db, provider.get_provider_name(), False, None, None, str(exc)
                )
                PROVIDER_FAILURES_TOTAL.labels(provider=provider.get_provider_name()).inc()
                PROVIDER_CONFIDENCE.labels(provider=provider.get_provider_name()).set(
                    row.provider_confidence
                )
        db.commit()
        SUCCESSFUL_COLLECTIONS.inc()
        agg = aggregate_btc_prices(points)
        return agg.__dict__

    def latest_points(self, db: Session, limit: int = 200) -> list[BTCPricePoint]:
        return list(
            db.execute(
                select(BTCPricePoint)
                .order_by(BTCPricePoint.observed_at.desc(), BTCPricePoint.id.desc())
                .limit(limit)
            ).scalars()
        )
