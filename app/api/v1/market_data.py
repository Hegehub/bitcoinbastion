from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.models.provider_health_record import ProviderHealthRecord
from app.services.market_data.market_data_service import MarketDataService

router = APIRouter(prefix="/market", tags=["market-data"])


@router.get("/btc/price")
def btc_price(db: Session = Depends(db_session)) -> dict[str, object]:
    return {"data": MarketDataService().collect_btc_price(db)}


@router.get("/btc/providers")
def btc_providers(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = list(db.execute(select(ProviderHealthRecord).order_by(ProviderHealthRecord.provider.asc())).scalars())
    return {"data": [{"provider": r.provider, "provider_confidence": r.provider_confidence, "is_degraded": r.is_degraded} for r in rows]}


@router.get("/btc/providers/health")
def btc_providers_health(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = list(db.execute(select(ProviderHealthRecord).order_by(ProviderHealthRecord.provider.asc())).scalars())
    return {"data": [{"provider": r.provider, "last_success_at": r.last_success_at, "last_failure_at": r.last_failure_at, "failure_count": r.failure_count, "success_count": r.success_count, "avg_latency_ms": r.avg_latency_ms, "provider_confidence": r.provider_confidence, "is_degraded": r.is_degraded} for r in rows]}


@router.get("/btc/price/history")
def btc_price_history(db: Session = Depends(db_session), limit: int = 200) -> dict[str, object]:
    rows = MarketDataService().latest_points(db, limit=limit)
    return {"data": [{"provider": r.provider, "pair": r.pair, "price_usd": r.price_usd, "observed_at": r.observed_at, "provider_confidence": r.provider_confidence} for r in rows]}
