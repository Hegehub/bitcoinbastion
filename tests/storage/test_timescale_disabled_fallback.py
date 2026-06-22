from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.db.models.btc_candle import BTCCandle
from app.db.models.btc_price_point import BTCPricePoint
from app.db.models.mempool_fee_snapshot import MempoolFeeSnapshot
from app.storage.timeseries.health import check_timescale


def test_timescale_disabled_fallback_uses_plain_sqlalchemy_tables() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert BTCPricePoint.__table__.name in Base.metadata.tables
    assert BTCCandle.__table__.name in Base.metadata.tables
    assert MempoolFeeSnapshot.__table__.name in Base.metadata.tables

    with Session(engine) as session:
        status = check_timescale(Settings(_env_file=None, TIMESCALE_ENABLED=False), session)

    assert status.status == "disabled"
    assert status.details["enabled"] is False
    assert status.details["extension_available"] is None
    assert status.details["hypertables"] == {}


def test_timescale_market_tables_have_timeseries_indexes() -> None:
    price_indexes = {idx.name for idx in BTCPricePoint.__table__.indexes}
    candle_indexes = {idx.name for idx in BTCCandle.__table__.indexes}
    mempool_indexes = {idx.name for idx in MempoolFeeSnapshot.__table__.indexes}

    assert "ix_btc_price_points_pair_observed_at" in price_indexes
    assert "ix_btc_price_points_provider_observed_at" in price_indexes
    assert "ix_btc_candles_timeframe_open_time" in candle_indexes
    assert "ix_mempool_fee_snapshots_source_observed_at" in mempool_indexes
