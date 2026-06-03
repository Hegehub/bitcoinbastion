from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.market_pattern import MarketPattern
from app.db.models.news_event import NewsEvent
from app.services.intelligence.market_memory.types import PatternMatch
from app.services.intelligence.market_memory_service import MarketMemoryService, PatternCandidate

SUPPORTED_PATTERN_NAMES = [
    "ETF inflow shock",
    "ETF outflow shock",
    "Fed liquidity shock",
    "SEC enforcement",
    "Regulatory approval",
    "Exchange hack",
    "Security incident",
    "Miner capitulation",
    "Institutional adoption",
    "Treasury adoption",
    "Lightning adoption",
    "Bitcoin Core release",
    "Macro risk-on",
    "Macro risk-off",
    "Large liquidation cascade",
]


class PatternMatcher:
    """Explicit, auditable pattern matcher; no hidden classifications."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.memory = MarketMemoryService(db)

    def supported_patterns(self) -> list[str]:
        self.memory.ensure_patterns()
        return SUPPORTED_PATTERN_NAMES.copy()

    def match_event(self, event_id: int, *, persist: bool = True) -> list[PatternMatch]:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return []
        candidates = self.memory.classify_event(event, persist=persist)
        return [self._to_match(candidate) for candidate in candidates]

    def _to_match(self, candidate: PatternCandidate) -> PatternMatch:
        return PatternMatch(
            pattern_id=candidate.pattern.id,
            pattern_slug=candidate.pattern.slug,
            pattern_name=candidate.pattern.name,
            confidence_score=round(candidate.confidence, 6),
            reason_codes=candidate.reasons,
        )

    def get_pattern(self, pattern: str) -> MarketPattern | None:
        return self.memory.get_pattern(pattern)
