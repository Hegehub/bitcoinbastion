from typing import Any

from celery import shared_task

from app.db.session import SessionLocal
from app.services.market.collector import BTCPriceCollector


@shared_task(name="market.collect_btc_price", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def market_collect_btc_price(self: Any) -> dict[str, object]:
    with SessionLocal() as db:
        return BTCPriceCollector().collect(db).__dict__
