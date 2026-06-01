from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.btc_price_point import BTCPricePoint
from app.services.market.candles.builder import BTCCandleBuilderService


def test_1m_candle_generation() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        t = datetime(2026, 5, 26, 14, 0, 10, tzinfo=UTC)
        db.add(BTCPricePoint(provider="binance", provider_name="binance", pair="BTCUSD", symbol="BTC", price_usd=100.0, observed_at=t, raw_payload_hash="h1"))
        db.add(BTCPricePoint(provider="kraken", provider_name="kraken", pair="BTCUSD", symbol="BTC", price_usd=101.0, observed_at=t, raw_payload_hash="h2"))
        db.commit()
        candle = BTCCandleBuilderService().build_candle(db, "1m", t)
        assert candle is not None
        assert candle.open == 100.0
        assert candle.close == 101.0


def test_deterministic_rebuild() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        t = datetime(2026, 5, 26, 14, 5, 10, tzinfo=UTC)
        db.add(BTCPricePoint(provider="binance", provider_name="binance", pair="BTCUSD", symbol="BTC", price_usd=100.0, observed_at=t, raw_payload_hash="h1"))
        db.commit()
        svc = BTCCandleBuilderService()
        first = svc.build_candle(db, "1m", t)
        second = svc.rebuild_candle(db, "1m", t)
        assert first is not None and second is not None
        assert first.open == second.open
