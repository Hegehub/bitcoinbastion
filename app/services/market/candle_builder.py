from __future__ import annotations
import time
from datetime import UTC, datetime
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.btc_candle import BTCCandle
from app.db.models.btc_price_point import BTCPricePoint
from app.db.models.candle_build_run import CandleBuildRun
from app.db.models.candle_provider_snapshot import CandleProviderSnapshot
from app.services.market.candle_confidence import calculate_candle_provider_confidence
from app.services.market.candles.timeframes import align_window
from app.services.market.market_regime import classify_market_regime

class MarketCandleBuilderService:
    def build(self, db: Session, timeframe: str, at: datetime) -> BTCCandle | None:
        started = time.perf_counter()
        start, end = align_window(at, timeframe)
        points = list(db.execute(select(BTCPricePoint).where(BTCPricePoint.observed_at >= start, BTCPricePoint.observed_at <= end).order_by(BTCPricePoint.observed_at.asc())).scalars())
        if not points:
            db.add(CandleBuildRun(timeframe=timeframe, window_start=start, window_end=end, build_status="no_data"))
            db.commit()
            return None
        prices = [p.price_usd for p in points if p.price_usd > 0]
        providers = {p.provider_name or p.provider for p in points}
        op, cl = prices[0], prices[-1]
        hi, lo = max(prices), min(prices)
        med = median(prices)
        disagreement = ((hi-lo)/med) if med else 0.0
        degraded = len(providers) <= 1 or disagreement > 0.02
        conf = calculate_candle_provider_confidence(len(providers), disagreement, degraded)
        vol_score = min(1.0, abs(hi-lo)/med if med else 0.0)
        regime = classify_market_regime(vol_score, disagreement)
        is_partial = datetime.now(UTC) <= end
        existing = db.execute(select(BTCCandle).where(BTCCandle.timeframe==timeframe, BTCCandle.open_time==start)).scalar_one_or_none()
        if existing is None:
            candle = BTCCandle(timeframe=timeframe, open_time=start, close_time=end, open=op, high=hi, low=lo, close=cl, volume=None, price_source_mode="median_multi_provider", provider_count=len(providers), provider_confidence=conf, provider_disagreement_score=disagreement, aggregation_method="hierarchical_v1", is_partial=is_partial, is_rebuilt=False, is_degraded=degraded, market_regime=regime, volatility_score=vol_score, evidence_packet_id="", provider_snapshot_json={"providers": list(providers)}, integrity_status="degraded" if degraded else "valid", integrity_notes="provider_disagreement" if disagreement>0.02 else "", is_finalized=not is_partial)
            db.add(candle)
            db.flush()
            for prv in providers:
                db.add(CandleProviderSnapshot(candle_id=candle.id, provider_name=prv, provider_price_open=op, provider_price_high=hi, provider_price_low=lo, provider_price_close=cl, provider_confidence=conf))
        duration = int((time.perf_counter()-started)*1000)
        db.add(CandleBuildRun(timeframe=timeframe, window_start=start, window_end=end, source_point_count=len(points), provider_count=len(providers), provider_confidence=conf, build_status="ok", build_duration_ms=duration, degraded_reason="single_provider_mode" if len(providers)<=1 else "provider_disagreement" if disagreement>0.02 else ""))
        db.commit()
        return db.execute(select(BTCCandle).where(BTCCandle.timeframe==timeframe, BTCCandle.open_time==start)).scalar_one_or_none()
