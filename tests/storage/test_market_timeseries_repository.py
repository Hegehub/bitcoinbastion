from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.services.market.timeseries_repository import MarketTimeSeriesRepository


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_repository_inserts_and_reads_price_points_in_bounded_order() -> None:
    db = _session()
    repo = MarketTimeSeriesRepository(db)
    start = datetime(2026, 1, 1, tzinfo=UTC)

    repo.bulk_insert_price_points(
        [
            {
                "provider": "kraken",
                "pair": "BTCUSD",
                "price_usd": 102.0,
                "observed_at": start + timedelta(minutes=2),
                "raw_payload_hash": "b" * 64,
            },
            {
                "provider": "kraken",
                "pair": "BTCUSD",
                "price_usd": 101.0,
                "observed_at": start + timedelta(minutes=1),
                "raw_payload_hash": "a" * 64,
            },
        ]
    )
    db.commit()

    rows = repo.get_price_points_range(
        start=start,
        end=start + timedelta(minutes=3),
        pair="BTCUSD",
        provider="kraken",
        limit=10,
    )

    assert [row.price_usd for row in rows] == [101.0, 102.0]
    assert repo.get_latest_price_point(pair="BTCUSD", provider="kraken").price_usd == 102.0


def test_repository_inserts_and_reads_candles_in_bounded_order() -> None:
    db = _session()
    repo = MarketTimeSeriesRepository(db)
    start = datetime(2026, 1, 1, tzinfo=UTC)

    repo.bulk_insert_candles(
        [
            {
                "timeframe": "1m",
                "open_time": start + timedelta(minutes=2),
                "close_time": start + timedelta(minutes=3),
                "open": 102.0,
                "high": 103.0,
                "low": 101.0,
                "close": 102.5,
            },
            {
                "timeframe": "1m",
                "open_time": start + timedelta(minutes=1),
                "close_time": start + timedelta(minutes=2),
                "open": 101.0,
                "high": 102.0,
                "low": 100.0,
                "close": 101.5,
            },
        ]
    )
    db.commit()

    candles = repo.get_candles_range(
        start=start,
        end=start + timedelta(minutes=5),
        timeframe="1m",
        limit=10,
    )

    assert [candle.open for candle in candles] == [101.0, 102.0]
    assert repo.get_latest_candle(timeframe="1m").open == 102.0


def test_repository_inserts_and_reads_mempool_fee_snapshots() -> None:
    db = _session()
    repo = MarketTimeSeriesRepository(db)
    start = datetime(2026, 1, 1, tzinfo=UTC)

    repo.insert_mempool_fee_snapshot(
        source="mempool-space",
        observed_at=start + timedelta(minutes=1),
        fastest_fee_sat_vb=25.0,
        half_hour_fee_sat_vb=18.0,
    )
    repo.insert_mempool_fee_snapshot(
        source="mempool-space",
        observed_at=start + timedelta(minutes=2),
        fastest_fee_sat_vb=30.0,
        half_hour_fee_sat_vb=20.0,
    )
    db.commit()

    rows = repo.get_mempool_fee_snapshots_range(
        start=start,
        end=start + timedelta(minutes=3),
        source="mempool-space",
        limit=10,
    )

    assert [row.fastest_fee_sat_vb for row in rows] == [25.0, 30.0]
