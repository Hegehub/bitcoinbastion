from __future__ import annotations

from statistics import mean

from sqlalchemy.orm import Session

from app.db.models.event_fingerprint import EventFingerprintRecord
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.services.intelligence.market_memory.types import EventFingerprint


class EventFingerprintBuilder:
    """Builds deterministic Bitcoin-first fingerprints for historical comparison."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, event_id: int, *, persist: bool = True) -> EventFingerprint | None:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return None
        impact = self.db.query(NewsPriceImpact).filter(NewsPriceImpact.event_id == event_id).first()
        fingerprint = EventFingerprint(
            event_id=event.id,
            btc_relevance_score=self._clamp(event.btc_relevance_score),
            market_impact_score=self._clamp(event.market_impact_score),
            sentiment_score=self._sentiment_score(event.event_sentiment),
            institutional_score=self._flag_score(event.is_institutional_related),
            macro_score=self._flag_score(event.is_macro_related),
            regulatory_score=self._flag_score(event.is_regulatory_related),
            security_score=self._flag_score(event.is_security_related),
            source_count=int(event.source_count or event.article_count or 0),
            price_change_15m=impact.change_15m_pct if impact else None,
            price_change_1h=impact.change_1h_pct if impact else None,
            price_change_4h=impact.change_4h_pct if impact else None,
            price_change_24h=impact.change_24h_pct if impact else None,
            direction=self._direction(impact),
            volatility_profile={
                "volatility_context": impact.volatility_context if impact else 0.0,
                "dominant_window": impact.dominant_window if impact else "UNKNOWN",
                "impact_band": impact.impact_band if impact else "UNKNOWN",
            },
            confidence_score=self._confidence(event, impact),
        )
        if persist:
            self._persist(fingerprint)
        return fingerprint

    def _persist(self, fingerprint: EventFingerprint) -> None:
        row = (
            self.db.query(EventFingerprintRecord)
            .filter(EventFingerprintRecord.event_id == fingerprint.event_id)
            .first()
        )
        payload = fingerprint.__dict__.copy()
        if row is None:
            row = EventFingerprintRecord(**payload)
            self.db.add(row)
        else:
            for key, value in payload.items():
                setattr(row, key, value)
        self.db.flush()

    def _direction(self, impact: NewsPriceImpact | None) -> str:
        if impact is None:
            return "UNKNOWN"
        if impact.actual_direction and impact.actual_direction.upper() != "UNKNOWN":
            return impact.actual_direction.upper()
        values = [
            impact.change_15m_pct,
            impact.change_1h_pct,
            impact.change_4h_pct,
            impact.change_24h_pct,
        ]
        numeric = [value for value in values if value is not None]
        if not numeric:
            return "UNKNOWN"
        total = sum(numeric)
        if total > 0:
            return "UP"
        if total < 0:
            return "DOWN"
        return "FLAT"

    def _confidence(self, event: NewsEvent, impact: NewsPriceImpact | None) -> float:
        values = [event.event_confidence, event.provider_confidence]
        if impact is not None:
            values.extend([impact.provider_confidence, impact.impact_confidence_score])
        numeric = [self._clamp(value) for value in values if value is not None]
        return round(mean(numeric), 6) if numeric else 0.0

    def _sentiment_score(self, sentiment: str | None) -> float:
        value = (sentiment or "UNKNOWN").upper()
        if value == "POSITIVE":
            return 1.0
        if value == "NEGATIVE":
            return -1.0
        if value == "NEUTRAL":
            return 0.0
        return 0.0

    def _flag_score(self, value: bool | None) -> float:
        return 1.0 if bool(value) else 0.0

    def _clamp(self, value: float | None) -> float:
        return round(max(0.0, min(1.0, float(value or 0.0))), 6)
