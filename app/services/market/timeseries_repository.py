from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.btc_candle import BTCCandle
from app.db.models.btc_price_point import BTCPricePoint
from app.db.models.mempool_fee_snapshot import MempoolFeeSnapshot


class MarketTimeSeriesRepository:
    """Bounded repository for operational BTC market time-series data.

    This repository works with normal PostgreSQL/SQLite tables and with the same
    tables after TimescaleDB converts them to hypertables. It does not write to
    ClickHouse, Redis, or any other projection target.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def insert_price_point(self, **values: Any) -> BTCPricePoint:
        point = BTCPricePoint(**values)
        self.db.add(point)
        return point

    def bulk_insert_price_points(
        self, points: Iterable[BTCPricePoint | dict[str, Any]]
    ) -> list[BTCPricePoint]:
        rows = [
            point if isinstance(point, BTCPricePoint) else BTCPricePoint(**point)
            for point in points
        ]
        self.db.add_all(rows)
        return rows

    def get_price_points_range(
        self,
        *,
        start: datetime,
        end: datetime,
        pair: str | None = None,
        provider: str | None = None,
        limit: int = 1000,
    ) -> list[BTCPricePoint]:
        stmt = select(BTCPricePoint).where(
            BTCPricePoint.observed_at >= start,
            BTCPricePoint.observed_at < end,
        )
        if pair is not None:
            stmt = stmt.where(BTCPricePoint.pair == pair)
        if provider is not None:
            stmt = stmt.where(BTCPricePoint.provider == provider)
        stmt = stmt.order_by(BTCPricePoint.observed_at.asc(), BTCPricePoint.id.asc()).limit(limit)
        return list(self.db.execute(stmt).scalars())

    def get_latest_price_point(
        self,
        *,
        pair: str | None = None,
        provider: str | None = None,
    ) -> BTCPricePoint | None:
        stmt = select(BTCPricePoint)
        if pair is not None:
            stmt = stmt.where(BTCPricePoint.pair == pair)
        if provider is not None:
            stmt = stmt.where(BTCPricePoint.provider == provider)
        stmt = stmt.order_by(BTCPricePoint.observed_at.desc(), BTCPricePoint.id.desc()).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def insert_candle(self, **values: Any) -> BTCCandle:
        candle = BTCCandle(**values)
        self.db.add(candle)
        return candle

    def bulk_insert_candles(self, candles: Iterable[BTCCandle | dict[str, Any]]) -> list[BTCCandle]:
        rows = [
            candle if isinstance(candle, BTCCandle) else BTCCandle(**candle) for candle in candles
        ]
        self.db.add_all(rows)
        return rows

    def get_candles_range(
        self,
        *,
        start: datetime,
        end: datetime,
        timeframe: str | None = None,
        limit: int = 1000,
    ) -> list[BTCCandle]:
        stmt = select(BTCCandle).where(
            BTCCandle.open_time >= start,
            BTCCandle.open_time < end,
        )
        if timeframe is not None:
            stmt = stmt.where(BTCCandle.timeframe == timeframe)
        stmt = stmt.order_by(BTCCandle.open_time.asc(), BTCCandle.id.asc()).limit(limit)
        return list(self.db.execute(stmt).scalars())

    def get_latest_candle(self, *, timeframe: str | None = None) -> BTCCandle | None:
        stmt = select(BTCCandle)
        if timeframe is not None:
            stmt = stmt.where(BTCCandle.timeframe == timeframe)
        stmt = stmt.order_by(BTCCandle.open_time.desc(), BTCCandle.id.desc()).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def insert_mempool_fee_snapshot(self, **values: Any) -> MempoolFeeSnapshot:
        snapshot = MempoolFeeSnapshot(**values)
        self.db.add(snapshot)
        return snapshot

    def get_mempool_fee_snapshots_range(
        self,
        *,
        start: datetime,
        end: datetime,
        source: str | None = None,
        limit: int = 1000,
    ) -> list[MempoolFeeSnapshot]:
        stmt = select(MempoolFeeSnapshot).where(
            MempoolFeeSnapshot.observed_at >= start,
            MempoolFeeSnapshot.observed_at < end,
        )
        if source is not None:
            stmt = stmt.where(MempoolFeeSnapshot.source == source)
        stmt = stmt.order_by(
            MempoolFeeSnapshot.observed_at.asc(), MempoolFeeSnapshot.id.asc()
        ).limit(limit)
        return list(self.db.execute(stmt).scalars())
