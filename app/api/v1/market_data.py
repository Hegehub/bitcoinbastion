from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.models.provider_health_record import ProviderHealthRecord
from app.services.market_data.market_data_service import MarketDataService
from app.schemas.market_data import BTCMarketOverviewEnvelope, BTCMarketOverviewOut

router = APIRouter(prefix="/market", tags=["market-data"])


@router.get("/btc/price", response_model=BTCMarketOverviewEnvelope)
def btc_price(db: Session = Depends(db_session)) -> BTCMarketOverviewEnvelope:
    raw = MarketDataService().collect_btc_price(db)
    return BTCMarketOverviewEnvelope(
        data=BTCMarketOverviewOut(
            symbol=str(raw.get("symbol") or "BTC"),
            pair=str(raw.get("pair") or "BTCUSD"),
            price_usd=raw.get("price_usd"),
            observed_at=raw.get("observed_at"),
            provider_count=int(raw.get("provider_count") or 0),
            provider_confidence=raw.get("provider_confidence"),
            source="market-data-aggregation",
            limitations=[str(value) for value in raw.get("limitations", [])]
            if isinstance(raw.get("limitations"), list)
            else [],
        )
    )


@router.get(
    "/overview", response_model=BTCMarketOverviewEnvelope, operation_id="market_current_overview"
)
def market_overview(db: Session = Depends(db_session)) -> BTCMarketOverviewEnvelope:
    points = MarketDataService().latest_points(db, limit=1)
    point = points[0] if points else None
    return BTCMarketOverviewEnvelope(
        data=BTCMarketOverviewOut(
            symbol="BTC",
            pair=point.pair if point is not None else "BTCUSD",
            price_usd=point.price_usd if point is not None else None,
            observed_at=point.observed_at if point is not None else None,
            provider_count=1 if point is not None else 0,
            provider_confidence=point.provider_confidence if point is not None else None,
            source=point.provider if point is not None else "market-data-store",
            limitations=[]
            if point is not None
            else ["No persisted market observation is available."],
        )
    )


@router.get("/btc/providers")
def btc_providers(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = list(
        db.execute(
            select(ProviderHealthRecord).order_by(ProviderHealthRecord.provider.asc())
        ).scalars()
    )
    return {
        "data": [
            {
                "provider": r.provider,
                "provider_confidence": r.provider_confidence,
                "is_degraded": r.is_degraded,
            }
            for r in rows
        ]
    }


@router.get("/btc/providers/health")
def btc_providers_health(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = list(
        db.execute(
            select(ProviderHealthRecord).order_by(ProviderHealthRecord.provider.asc())
        ).scalars()
    )
    return {
        "data": [
            {
                "provider": r.provider,
                "last_success_at": r.last_success_at,
                "last_failure_at": r.last_failure_at,
                "failure_count": r.failure_count,
                "success_count": r.success_count,
                "avg_latency_ms": r.avg_latency_ms,
                "provider_confidence": r.provider_confidence,
                "is_degraded": r.is_degraded,
            }
            for r in rows
        ]
    }


@router.get("/btc/price/history")
def btc_price_history(db: Session = Depends(db_session), limit: int = 200) -> dict[str, object]:
    rows = MarketDataService().latest_points(db, limit=limit)
    return {
        "data": [
            {
                "provider": r.provider,
                "pair": r.pair,
                "price_usd": r.price_usd,
                "observed_at": r.observed_at,
                "provider_confidence": r.provider_confidence,
            }
            for r in rows
        ]
    }
