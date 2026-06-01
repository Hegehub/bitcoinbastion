from datetime import datetime
from typing import Any

from app.db.models.time_utils import utcnow
from pydantic import BaseModel, Field


class CandleAttributionCandidateResponse(BaseModel):
    event_id: int | None = None
    article_id: int | None = None
    rank: int
    confidence: float
    confidence_band: str
    direction_match: str
    time_distance_seconds: int
    summary: str
    explanation: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class CandleAttributionResponse(BaseModel):
    candle: dict[str, Any] | None = None
    candidate_events: list[CandleAttributionCandidateResponse] = Field(default_factory=list)
    ranking: list[CandleAttributionCandidateResponse] = Field(default_factory=list)
    confidence: float = 0.0
    summary: str = ""
    limitations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utcnow)
