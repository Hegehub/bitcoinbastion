from dataclasses import dataclass
from math import fabs

from app.core.config import get_settings
from app.db.models.btc_candle import BTCCandle
from app.db.models.news_event import NewsEvent
from app.services.intelligence.candle_attribution.enums import AttributionType, CandidateCategory


@dataclass(frozen=True)
class ScoredCandidate:
    event: NewsEvent
    article_id: int | None
    attribution_type: str
    candidate_category: str
    time_distance_seconds: int
    time_distance_weight: float
    price_move_pct: float
    direction_match: bool
    event_score: float
    impact_score: float
    confidence_score: float
    provider_confidence: float
    source_confidence: float
    window_used: str
    dominant_window: str
    rank: int = 0


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


class AttributionScoringService:
    """Scores candidate events without asserting direct market causation."""

    def __init__(self) -> None:
        self.max_confidence = float(get_settings().attribution_max_confidence)

    def price_move_pct(self, candle: BTCCandle) -> float:
        if candle.open is None or candle.close is None or candle.open <= 0:
            return 0.0
        return ((candle.close - candle.open) / candle.open) * 100.0

    def candle_direction(self, candle: BTCCandle) -> str:
        move = self.price_move_pct(candle)
        threshold = float(get_settings().market_flat_threshold_pct)
        if fabs(move) < threshold:
            return "FLAT"
        return "UP" if move > 0 else "DOWN"

    def time_distance_seconds(self, candle: BTCCandle, event: NewsEvent) -> int:
        if candle.open_time <= event.first_seen_at <= candle.close_time:
            return 0
        if event.first_seen_at < candle.open_time:
            return int((candle.open_time - event.first_seen_at).total_seconds())
        return int((event.first_seen_at - candle.close_time).total_seconds())

    def time_distance_weight(self, distance_seconds: int) -> float:
        minutes = max(0.0, distance_seconds / 60.0)
        if minutes <= 15:
            return 1.0 - (minutes / 15.0) * 0.05
        if minutes <= 60:
            return 0.95 - ((minutes - 15.0) / 45.0) * 0.25
        if minutes <= 240:
            return 0.70 - ((minutes - 60.0) / 180.0) * 0.40
        return 0.20

    def direction_match(self, candle: BTCCandle, event: NewsEvent) -> bool:
        candle_direction = self.candle_direction(candle)
        sentiment = (event.event_sentiment or "UNKNOWN").upper()
        if candle_direction == "FLAT":
            return sentiment in {"NEUTRAL", "UNCERTAIN", "UNKNOWN", "MIXED"}
        if sentiment == "POSITIVE":
            return candle_direction == "UP"
        if sentiment == "NEGATIVE":
            return candle_direction == "DOWN"
        return False

    def direction_match_weight(self, candle: BTCCandle, event: NewsEvent) -> float:
        if self.direction_match(candle, event):
            return 1.0
        if self.candle_direction(candle) == "FLAT":
            return 0.75
        return 0.55

    def classify_category(self, event: NewsEvent) -> str:
        text = f"{event.event_category} {event.event_type} {event.canonical_title}".lower()
        if "etf" in text:
            return CandidateCategory.ETF.value
        if "fed" in text or "macro" in text:
            return CandidateCategory.FED.value if "fed" in text else CandidateCategory.MACRO.value
        if "sec" in text or "regulat" in text:
            return CandidateCategory.SEC.value
        if "exchange" in text:
            return CandidateCategory.EXCHANGE.value
        if "mining" in text or "miner" in text:
            return CandidateCategory.MINING.value
        if "lightning" in text:
            return CandidateCategory.LIGHTNING.value
        if "core" in text:
            return CandidateCategory.BITCOIN_CORE.value
        if "security" in text or event.is_security_related:
            return CandidateCategory.SECURITY.value
        if "liquidity" in text:
            return CandidateCategory.LIQUIDITY.value
        if "treasury" in text:
            return CandidateCategory.TREASURY.value
        if "adoption" in text:
            return CandidateCategory.ADOPTION.value
        return CandidateCategory.UNKNOWN.value

    def classify_type(self, event: NewsEvent) -> str:
        if event.is_security_related:
            return AttributionType.SECURITY_EVENT.value
        if event.is_regulatory_related:
            return AttributionType.REGULATORY_EVENT.value
        if event.is_macro_related:
            return AttributionType.MACRO_EVENT.value
        if event.is_institutional_related:
            return AttributionType.INSTITUTIONAL_EVENT.value
        return AttributionType.NEWS_EVENT.value

    def score_candidate(self, candle: BTCCandle, event: NewsEvent) -> ScoredCandidate:
        distance = self.time_distance_seconds(candle, event)
        time_weight = self.time_distance_weight(distance)
        provider_confidence = clamp(float(event.provider_confidence or 0.5))
        source_confidence = clamp(float(event.cluster_confidence or event.event_confidence or 0.5))
        event_confidence = clamp(float(event.event_confidence or source_confidence))
        btc_relevance = clamp(float(event.btc_relevance_score or 0.0))
        market_impact = clamp(float(event.market_impact_score or 0.0))
        match_weight = self.direction_match_weight(candle, event)
        raw_score = (
            event_confidence
            * btc_relevance
            * market_impact
            * source_confidence
            * provider_confidence
            * time_weight
            * match_weight
        )
        confidence = min(self.max_confidence, clamp(raw_score))
        return ScoredCandidate(
            event=event,
            article_id=event.primary_article_id,
            attribution_type=self.classify_type(event),
            candidate_category=self.classify_category(event),
            time_distance_seconds=distance,
            time_distance_weight=round(time_weight, 4),
            price_move_pct=round(self.price_move_pct(candle), 6),
            direction_match=self.direction_match(candle, event),
            event_score=event_confidence,
            impact_score=market_impact,
            confidence_score=round(confidence, 6),
            provider_confidence=provider_confidence,
            source_confidence=source_confidence,
            window_used="inside" if distance == 0 else "nearby",
            dominant_window="candle" if distance == 0 else "pre_post_window",
        )
