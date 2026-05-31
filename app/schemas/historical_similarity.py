from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.models.time_utils import utcnow


class HistoricalSimilarityReport(BaseModel):
    reference_event: dict[str, Any] | None = None
    similar_events: list[dict[str, Any]] = Field(default_factory=list)
    similarity_band: str = "Weak"
    sample_size: int = 0
    median_reaction_15m: float | None = None
    median_reaction_1h: float | None = None
    median_reaction_4h: float | None = None
    median_reaction_24h: float | None = None
    average_reaction_15m: float | None = None
    average_reaction_1h: float | None = None
    average_reaction_4h: float | None = None
    average_reaction_24h: float | None = None
    confidence: float = 0.0
    limitations: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utcnow)
