from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.btc_candle import BTCCandle
from app.db.models.btc_price_point import BTCPricePoint
from app.services.market.candles.aggregator import ohlc, spread_pct
from app.services.market.candles.integrity import calculate_integrity_score, evaluate_integrity
from app.services.market.candles.provider_confidence import calculate_provider_confidence
from app.services.market.candles.timeframes import align_window


class BTCCandleBuilderService:
    def build_candle(self, db: Session, timeframe: str, open_time: datetime) -> BTCCandle | None:
        start, end = align_window(open_time, timeframe)
        points = list(db.execute(select(BTCPricePoint).where(BTCPricePoint.observed_at >= start, BTCPricePoint.observed_at <= end).order_by(BTCPricePoint.observed_at.asc())).scalars())
        if not points:
            return None
        prices = [p.price_usd for p in points if p.price_usd > 0]
        if not prices:
            return None
        op, hi, lo, cl = ohlc(prices)
        providers = {p.provider_name or p.provider for p in points}
        spread = spread_pct(prices)
        is_partial = datetime.now(UTC) <= end
        degraded = len(providers) <= 1 or spread > 2.5
        pconf = calculate_provider_confidence(len(providers), spread, degraded)
        integrity_score = calculate_integrity_score(len(providers), len(points), spread, degraded)
        integrity_status, integrity_notes = evaluate_integrity(len(providers), spread, is_partial)
        mode = "single_provider" if len(providers) <= 1 else "fallback_provider" if spread > 2.5 else "median_multi_provider"
        existing = db.execute(select(BTCCandle).where(BTCCandle.timeframe == timeframe, BTCCandle.open_time == start)).scalar_one_or_none()
        if existing:
            return existing
        candle = BTCCandle(
            timeframe=timeframe,
            open_time=start,
            close_time=end,
            open=op,
            high=hi,
            low=lo,
            close=cl,
            volume=float(len(points)),
            price_source_mode=mode,
            provider_count=len(providers),
            provider_confidence=pconf,
            provider_snapshot_json={"providers": list(providers), "points": len(points), "spread_pct": round(spread, 4)},
            integrity_status=integrity_status,
            integrity_notes=integrity_notes,
            is_partial=is_partial,
            is_finalized=not is_partial,
            rebuild_reason="",
            metadata_json={"integrity_score": integrity_score},
        )
        db.add(candle)
        db.commit()
        return candle

    def rebuild_candle(self, db: Session, timeframe: str, open_time: datetime, reason: str = "manual_rebuild") -> BTCCandle | None:
        candle = self.build_candle(db, timeframe, open_time)
        if candle is not None:
            candle.revision += 1
            candle.rebuild_reason = reason
            candle.rebuilt_at = datetime.now(UTC)
            candle.price_source_mode = "reconstructed"
            db.commit()
        return candle
