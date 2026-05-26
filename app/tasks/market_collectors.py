from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.provider_health_record import ProviderHealthRecord
from app.db.session import SessionLocal
from app.services.market_data.market_data_service import MarketDataService


@shared_task(name="market.collect_btc_price", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def collect_btc_price_task(self: Any) -> dict[str, object]:
    with SessionLocal() as db:
        return MarketDataService().collect_btc_price(db)


@shared_task(name="market.refresh_provider_health", bind=True)  # type: ignore[untyped-decorator]
def refresh_provider_health_task(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        rows = list(db.execute(select(ProviderHealthRecord)).scalars())
        degraded = sum(1 for r in rows if r.is_degraded)
        return {"providers": len(rows), "degraded": degraded}
