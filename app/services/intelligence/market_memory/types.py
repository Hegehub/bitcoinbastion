from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MarketMemoryRecord:
    id: int | None
    event_id: int
    pattern_id: int
    memory_type: str
    memory_score: float
    confidence_score: float
    created_at: datetime | None = None


@dataclass(frozen=True)
class EventFingerprint:
    event_id: int
    btc_relevance_score: float
    market_impact_score: float
    sentiment_score: float
    institutional_score: float
    macro_score: float
    regulatory_score: float
    security_score: float
    source_count: int
    price_change_15m: float | None
    price_change_1h: float | None
    price_change_4h: float | None
    price_change_24h: float | None
    direction: str
    volatility_profile: dict[str, Any]
    confidence_score: float


@dataclass(frozen=True)
class PatternMatch:
    pattern_id: int
    pattern_slug: str
    pattern_name: str
    confidence_score: float
    reason_codes: list[str]


@dataclass(frozen=True)
class SimilarityResult:
    event_id: int
    similar_event_id: int
    similarity_score: float
    confidence_score: float
    reason_codes: list[str]


@dataclass(frozen=True)
class HistoricalReactionSummary:
    pattern: str
    occurrences: int
    median_move_15m: float | None
    median_move_1h: float | None
    median_move_4h: float | None
    median_move_24h: float | None
    best_case_move: float | None
    worst_case_move: float | None
    confidence: float
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketMemoryEvidence:
    event_id: int
    source_events: list[dict[str, Any]]
    similarity_calculations: list[dict[str, Any]]
    pattern_matches: list[dict[str, Any]]
    historical_reaction_summary: dict[str, Any]
    limitations: list[str]
    provider_confidence: float
    generated_at: datetime
