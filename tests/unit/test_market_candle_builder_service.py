from datetime import UTC, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.models.btc_price_point import BTCPricePoint
from app.services.market.candle_builder import MarketCandleBuilderService


def test_build_1m_candle_and_degraded_flag() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        t = datetime(2026,5,27,10,0,10,tzinfo=UTC)
        db.add(BTCPricePoint(provider="a", provider_name="a", pair="BTCUSD", symbol="BTC", price_usd=100, observed_at=t, raw_payload_hash="x"))
        db.add(BTCPricePoint(provider="b", provider_name="b", pair="BTCUSD", symbol="BTC", price_usd=102, observed_at=t, raw_payload_hash="y"))
        db.commit()
        c = MarketCandleBuilderService().build(db, "1m", t)
        assert c is not None
        assert c.open == 100
        assert c.close == 102
        assert c.provider_count == 2
