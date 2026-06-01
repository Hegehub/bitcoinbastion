from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.candle_attribution import CandleAttribution
from app.db.models.historical_event_profile import HistoricalEventProfile
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.services.intelligence.pattern_library import infer_pattern_type


@dataclass(frozen=True)
class HistoricalFeatureVector:
    narrative: tuple[str, str, str]
    market: tuple[float, float, float, float]
    scoring: tuple[float, float, float]
    context: tuple[float, float, float, float, float]


class HistoricalEventProfileBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_from_news_event(self, event: NewsEvent) -> HistoricalEventProfile:
        impact = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id == event.id)
            .order_by(NewsPriceImpact.id.desc())
            .first()
        )
        pattern = infer_pattern_type(event.canonical_title, event.event_type, event.event_category)
        return HistoricalEventProfile(
            event_type=event.event_type or "unknown",
            pattern_type=pattern.value,
            event_id=event.id,
            article_id=event.primary_article_id,
            canonical_title=event.canonical_title,
            primary_narrative=event.event_category or event.event_type or "unknown",
            sentiment_label=event.event_sentiment,
            btc_relevance_score=self._clamp(event.btc_relevance_score),
            market_impact_score=self._clamp(event.market_impact_score),
            institutional_score=1.0 if event.is_institutional_related else 0.0,
            macro_score=1.0 if event.is_macro_related else 0.0,
            security_score=1.0 if event.is_security_related else 0.0,
            regulatory_score=1.0 if event.is_regulatory_related else 0.0,
            sovereignty_score=self._sovereignty_score(event),
            confidence_score=self._clamp(event.event_confidence or event.cluster_confidence),
            price_change_15m_pct=impact.change_15m_pct if impact else None,
            price_change_1h_pct=impact.change_1h_pct if impact else None,
            price_change_4h_pct=impact.change_4h_pct if impact else None,
            price_change_24h_pct=impact.change_24h_pct if impact else None,
            provider_confidence=self._clamp(event.provider_confidence),
        )

    def build_from_price_impact(self, impact: NewsPriceImpact) -> HistoricalEventProfile:
        event = self.db.get(NewsEvent, impact.event_id) if impact.event_id else None
        if event is not None:
            profile = self.build_from_news_event(event)
            profile.price_change_15m_pct = impact.change_15m_pct
            profile.price_change_1h_pct = impact.change_1h_pct
            profile.price_change_4h_pct = impact.change_4h_pct
            profile.price_change_24h_pct = impact.change_24h_pct
            profile.confidence_score = self._clamp(impact.impact_confidence_score or impact.confidence_score)
            return profile
        pattern = infer_pattern_type(impact.sentiment_label)
        return HistoricalEventProfile(
            event_type="price_impact",
            pattern_type=pattern.value,
            event_id=impact.event_id,
            article_id=impact.article_id,
            canonical_title=f"Price impact {impact.id}",
            primary_narrative=impact.dominant_window,
            sentiment_label=impact.sentiment_label,
            btc_relevance_score=self._clamp(impact.btc_relevance_score),
            market_impact_score=self._clamp(impact.market_impact_score),
            confidence_score=self._clamp(impact.impact_confidence_score or impact.confidence_score),
            price_change_15m_pct=impact.change_15m_pct,
            price_change_1h_pct=impact.change_1h_pct,
            price_change_4h_pct=impact.change_4h_pct,
            price_change_24h_pct=impact.change_24h_pct,
            provider_confidence=self._clamp(impact.provider_confidence),
        )

    def build_from_candle_attribution(self, attribution: CandleAttribution) -> HistoricalEventProfile:
        event = self.db.get(NewsEvent, attribution.event_id) if attribution.event_id else None
        if event is not None:
            profile = self.build_from_news_event(event)
            profile.confidence_score = self._clamp(attribution.confidence_score)
            profile.provider_confidence = self._clamp(attribution.provider_confidence)
            return profile
        pattern = infer_pattern_type(attribution.summary_text, attribution.attribution_type, attribution.candidate_category)
        return HistoricalEventProfile(
            event_type=attribution.attribution_type,
            pattern_type=pattern.value,
            event_id=attribution.event_id,
            article_id=attribution.article_id,
            canonical_title=attribution.summary_text[:500],
            primary_narrative=attribution.candidate_category,
            sentiment_label=attribution.sentiment_direction_match,
            btc_relevance_score=self._clamp(attribution.btc_relevance_score),
            market_impact_score=self._clamp(attribution.market_impact_score),
            confidence_score=self._clamp(attribution.confidence_score),
            provider_confidence=self._clamp(attribution.provider_confidence),
        )

    def build_feature_vector(self, profile: HistoricalEventProfile) -> HistoricalFeatureVector:
        return HistoricalFeatureVector(
            narrative=(profile.event_type, profile.pattern_type, profile.primary_narrative),
            market=(
                profile.price_change_15m_pct or 0.0,
                profile.price_change_1h_pct or 0.0,
                profile.price_change_4h_pct or 0.0,
                profile.price_change_24h_pct or 0.0,
            ),
            scoring=(profile.btc_relevance_score, profile.market_impact_score, profile.confidence_score),
            context=(
                profile.institutional_score,
                profile.macro_score,
                profile.security_score,
                profile.regulatory_score,
                profile.sovereignty_score,
            ),
        )

    def _sovereignty_score(self, event: NewsEvent) -> float:
        text = f"{event.canonical_title} {event.canonical_summary}".lower()
        keywords = ["self-custody", "privacy", "open-source", "local node", "bitcoin core", "censorship"]
        return self._clamp(sum(1 for keyword in keywords if keyword in text) / 3.0)

    def _clamp(self, value: float | int | None) -> float:
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value)))
