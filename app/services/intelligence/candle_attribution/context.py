from app.db.models.btc_candle import BTCCandle
from app.services.intelligence.candle_attribution_engine import CandidateScore


class CandleContextBuilder:
    def summarize(self, candle: BTCCandle, candidates: list[CandidateScore]) -> dict[str, object]:
        return {
            "market_regime": candle.market_regime,
            "provider_confidence": candle.provider_confidence,
            "event_density": len(candidates),
            "positive_event_count": sum(
                1 for item in candidates if str(item.event.event_sentiment).upper() == "POSITIVE"
            ),
            "negative_event_count": sum(
                1 for item in candidates if str(item.event.event_sentiment).upper() == "NEGATIVE"
            ),
        }
