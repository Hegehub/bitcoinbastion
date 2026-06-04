from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.models.time_utils import utcnow


class HistoricalSimilarityResponse(BaseModel):
    current_item: dict[str, Any] | None = None
    matched_items: list[dict[str, Any]] = Field(default_factory=list)
    top_similar_events: list[dict[str, Any]] = Field(default_factory=list)
    pattern_detected: list[dict[str, Any]] = Field(default_factory=list)
    pattern_name: str | None = None
    pattern_category: str | None = None
    similarity_score: float = 0.0
    historical_matches: list[dict[str, Any]] = Field(default_factory=list)
    historical_median: dict[str, float | None] = Field(default_factory=dict)
    historical_average: dict[str, float | None] = Field(default_factory=dict)
    pattern_confidence: float = 0.0
    reaction_statistics: dict[str, Any] = Field(default_factory=dict)
    historical_reaction_summary: dict[str, Any] = Field(default_factory=dict)
    median_reaction: dict[str, float | None] = Field(default_factory=dict)
    reaction_summary: dict[str, Any] = Field(default_factory=dict)
    reaction_distribution: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    sample_size: int = 0
    similarity_band: str = "weak"
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utcnow)
