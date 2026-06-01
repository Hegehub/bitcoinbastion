from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.market_pattern_library import MarketPatternLibrary
from app.db.models.news_event import NewsEvent
from app.services.intelligence.historical_similarity_metrics import (
    PATTERN_CLASSIFICATION_FAILURES_TOTAL,
    PATTERN_CLASSIFICATIONS_TOTAL,
)
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.pattern_library import (
    MarketPattern,
    infer_pattern_type,
    seed_pattern_definitions,
)


@dataclass(frozen=True)
class PatternClassification:
    pattern_code: str
    confidence: float
    reasoning: list[str]


class PatternClassificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_pattern_library(self) -> list[MarketPatternLibrary]:
        existing = {row.pattern_code for row in self.db.query(MarketPatternLibrary).all()}
        rows: list[MarketPatternLibrary] = []
        for definition in seed_pattern_definitions():
            pattern_code = str(definition["pattern_code"])
            row = (
                self.db.query(MarketPatternLibrary)
                .filter(MarketPatternLibrary.pattern_code == pattern_code)
                .first()
            )
            if row is None and pattern_code not in existing:
                row = MarketPatternLibrary(**definition)
                self.db.add(row)
                existing.add(pattern_code)
            if row is not None:
                for key, value in definition.items():
                    if hasattr(row, key):
                        setattr(row, key, value)
                rows.append(row)
        self.db.flush()
        return (
            self.db.query(MarketPatternLibrary)
            .order_by(MarketPatternLibrary.pattern_code.asc())
            .all()
        )

    def classify_event(self, event: NewsEvent) -> list[PatternClassification]:
        try:
            inferred = infer_pattern_type(
                event.canonical_title, event.event_type, event.event_category
            )
            text = f"{event.canonical_title} {event.canonical_summary} {event.event_type} {event.event_category}".lower()
            classifications = [
                PatternClassification(
                    pattern_code=inferred.value,
                    confidence=self._confidence_for(inferred, text),
                    reasoning=self._reasoning_for(inferred, event),
                )
            ]
            for extra_pattern, keywords in {
                MarketPattern.SECURITY_INCIDENT: ["hack", "exploit", "malware", "security"],
                MarketPattern.MACRO_RISK_ON: ["risk-on", "easing", "liquidity"],
                MarketPattern.MACRO_RISK_OFF: ["risk-off", "tightening", "hawkish"],
                MarketPattern.VOLATILITY_EXPANSION: ["volatility", "breakout", "cascade"],
            }.items():
                if extra_pattern != inferred and any(keyword in text for keyword in keywords):
                    classifications.append(
                        PatternClassification(
                            pattern_code=extra_pattern.value,
                            confidence=0.58,
                            reasoning=[
                                f"matched secondary pattern keyword(s): {', '.join(keywords)}"
                            ],
                        )
                    )
            PATTERN_CLASSIFICATIONS_TOTAL.inc(len(classifications))
            return classifications
        except Exception:
            PATTERN_CLASSIFICATION_FAILURES_TOTAL.inc()
            raise

    def classification_evidence(self, event: NewsEvent) -> list[dict[str, object]]:
        return [
            {
                "pattern_code": item.pattern_code,
                "confidence": item.confidence,
                "reasoning": item.reasoning,
            }
            for item in self.classify_event(event)
        ]

    def classify_market_patterns(self, event: NewsEvent) -> list[dict[str, object]]:
        """Classify an event against the production market_patterns memory catalog."""
        candidates = MarketMemoryService(self.db).classify_event(event)
        return [
            {
                "pattern_id": item.pattern.id,
                "pattern_slug": item.pattern.slug,
                "pattern_name": item.pattern.name,
                "category": item.pattern.category,
                "confidence": item.confidence,
                "reasoning": item.reasons,
            }
            for item in candidates
        ]

    def _confidence_for(self, pattern: MarketPattern, text: str) -> float:
        if pattern == MarketPattern.UNKNOWN:
            return 0.35
        token = pattern.value.split("_")[0].lower()
        if token and token in text:
            return 0.86
        return 0.72

    def _reasoning_for(self, pattern: MarketPattern, event: NewsEvent) -> list[str]:
        if pattern == MarketPattern.UNKNOWN:
            return ["no high-confidence market pattern keywords matched"]
        return [
            f"classified from title/category as {pattern.value}",
            f"event_type={event.event_type}",
            f"event_category={event.event_category}",
        ]
