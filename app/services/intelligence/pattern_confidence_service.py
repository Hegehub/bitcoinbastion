from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from app.db.models.event_pattern_match import EventPatternMatch
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.services.intelligence.historical_similarity_metrics import (
    PATTERN_CONFIDENCE_CALCULATIONS_TOTAL,
)


@dataclass(frozen=True)
class PatternConfidenceBreakdown:
    sample_size: float
    source_diversity: float
    market_regime_diversity: float
    reaction_consistency: float
    provider_confidence: float
    event_freshness: float

    @property
    def score(self) -> float:
        value = (
            self.sample_size * 0.24
            + self.source_diversity * 0.16
            + self.market_regime_diversity * 0.14
            + self.reaction_consistency * 0.22
            + self.provider_confidence * 0.16
            + self.event_freshness * 0.08
        )
        return round(max(0.0, min(1.0, value)), 6)

    def as_dict(self) -> dict[str, float]:
        return {
            "sample_size": self.sample_size,
            "source_diversity": self.source_diversity,
            "market_regime_diversity": self.market_regime_diversity,
            "reaction_consistency": self.reaction_consistency,
            "provider_confidence": self.provider_confidence,
            "event_freshness": self.event_freshness,
            "score": self.score,
        }


class PatternConfidenceService:
    """Correlation-only confidence calculator for historical pattern memory."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate(self, pattern_id: int) -> PatternConfidenceBreakdown:
        PATTERN_CONFIDENCE_CALCULATIONS_TOTAL.inc()
        matches = (
            self.db.query(EventPatternMatch)
            .filter(EventPatternMatch.pattern_id == pattern_id)
            .order_by(EventPatternMatch.created_at.desc())
            .all()
        )
        event_ids = [row.event_id for row in matches]
        events = self.db.query(NewsEvent).filter(NewsEvent.id.in_(event_ids or [0])).all()
        impacts = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id.in_(event_ids or [0]))
            .all()
        )
        moves = [impact.change_4h_pct for impact in impacts if impact.change_4h_pct is not None]
        source_counts = [event.source_count for event in events]
        categories = {event.event_category for event in events if event.event_category}
        provider_values = [
            event.provider_confidence for event in events if event.provider_confidence is not None
        ]
        return PatternConfidenceBreakdown(
            sample_size=round(min(1.0, len(matches) / 20.0), 6),
            source_diversity=round(
                min(1.0, (mean(source_counts) if source_counts else 0.0) / 5.0), 6
            ),
            market_regime_diversity=round(min(1.0, len(categories) / 4.0), 6),
            reaction_consistency=self._reaction_consistency(moves),
            provider_confidence=round(mean(provider_values), 6) if provider_values else 0.0,
            event_freshness=1.0 if matches else 0.0,
        )

    def _reaction_consistency(self, moves: list[float]) -> float:
        if len(moves) <= 1:
            return 0.5 if moves else 0.0
        dispersion = pstdev(moves)
        return round(max(0.0, min(1.0, 1.0 - dispersion / 5.0)), 6)
