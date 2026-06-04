from __future__ import annotations

from statistics import mean, median

from sqlalchemy.orm import Session

from app.db.models.event_pattern_match import EventPatternMatch
from app.db.models.market_pattern import MarketPattern
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.pattern_statistics import PatternStatistics
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS
from app.services.intelligence.market_memory.types import HistoricalReactionSummary
from app.services.intelligence.market_memory_service import MarketMemoryService


class PatternStatisticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.memory = MarketMemoryService(db)

    def compute(self, pattern: str | int) -> HistoricalReactionSummary | None:
        pattern_row = self.memory.get_pattern(pattern)
        if pattern_row is None:
            return None
        matches = (
            self.db.query(EventPatternMatch)
            .filter(EventPatternMatch.pattern_id == pattern_row.id)
            .all()
        )
        event_ids = [row.event_id for row in matches]
        impacts = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id.in_(event_ids or [0]))
            .all()
        )
        moves_4h = [impact.change_4h_pct for impact in impacts if impact.change_4h_pct is not None]
        summary = HistoricalReactionSummary(
            pattern=pattern_row.slug,
            occurrences=len(matches),
            median_move_15m=self._median([impact.change_15m_pct for impact in impacts]),
            median_move_1h=self._median([impact.change_1h_pct for impact in impacts]),
            median_move_4h=self._median([impact.change_4h_pct for impact in impacts]),
            median_move_24h=self._median([impact.change_24h_pct for impact in impacts]),
            best_case_move=max(moves_4h) if moves_4h else None,
            worst_case_move=min(moves_4h) if moves_4h else None,
            confidence=self._average([row.classification_confidence for row in matches]),
            limitations=MARKET_MEMORY_SAFETY_LIMITATIONS.copy(),
        )
        self._persist(pattern_row, summary, matches, moves_4h, impacts)
        return summary

    def compute_all(self) -> list[HistoricalReactionSummary]:
        return [summary for pattern in self.memory.ensure_patterns() if (summary := self.compute(pattern.slug))]

    def payload(self, summary: HistoricalReactionSummary | None) -> dict[str, object] | None:
        if summary is None:
            return None
        return {
            "pattern": summary.pattern,
            "occurrences": summary.occurrences,
            "historical_occurrences": summary.occurrences,
            "median_move_15m": summary.median_move_15m,
            "median_move_1h": summary.median_move_1h,
            "median_move_4h": summary.median_move_4h,
            "median_move_24h": summary.median_move_24h,
            "best_case_move": summary.best_case_move,
            "worst_case_move": summary.worst_case_move,
            "confidence": summary.confidence,
            "limitations": summary.limitations,
        }

    def _persist(
        self,
        pattern: MarketPattern,
        summary: HistoricalReactionSummary,
        matches: list[EventPatternMatch],
        moves_4h: list[float],
        impacts: list[NewsPriceImpact],
    ) -> None:
        row = self.db.query(PatternStatistics).filter(PatternStatistics.pattern_id == pattern.id).first()
        if row is None:
            row = PatternStatistics(pattern_id=pattern.id)
            self.db.add(row)
        neutral = [value for value in moves_4h if abs(value) < 0.05]
        positive = [value for value in moves_4h if value > 0.05]
        negative = [value for value in moves_4h if value < -0.05]
        denom = len(moves_4h) or 1
        row.pattern_slug = pattern.slug
        row.historical_occurrences = summary.occurrences
        row.occurrence_count = summary.occurrences
        row.median_15m_move = summary.median_move_15m
        row.avg_move_15m = self._average([impact.change_15m_pct for impact in impacts])
        row.avg_move_1h = self._average([impact.change_1h_pct for impact in impacts])
        row.avg_move_4h = self._average([impact.change_4h_pct for impact in impacts])
        row.avg_move_24h = self._average([impact.change_24h_pct for impact in impacts])
        row.median_1h_move = summary.median_move_1h
        row.median_4h_move = summary.median_move_4h
        row.median_24h_move = summary.median_move_24h
        row.success_rate = round(len(positive) / denom, 6)
        row.positive_rate = round(len(positive) / denom, 6)
        row.negative_rate = round(len(negative) / denom, 6)
        row.neutral_rate = round(len(neutral) / denom, 6)
        row.average_confidence = self._average([m.classification_confidence for m in matches])
        row.best_case_move = summary.best_case_move
        row.worst_case_move = summary.worst_case_move
        self.db.flush()

    def _median(self, values: list[float | None]) -> float | None:
        numeric = [float(value) for value in values if value is not None]
        return round(float(median(numeric)), 6) if numeric else None

    def _average(self, values: list[float | None]) -> float:
        numeric = [float(value) for value in values if value is not None]
        return round(float(mean(numeric)), 6) if numeric else 0.0
