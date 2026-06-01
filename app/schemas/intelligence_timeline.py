from datetime import datetime
from pydantic import BaseModel


class TimelinePagination(BaseModel):
    limit: int
    offset: int
    total: int


class TimelineEventSummary(BaseModel):
    id: int
    event_type: str
    title: str
    event_time: datetime
    importance: str
    visibility: str


class TimelineEventResponse(TimelineEventSummary):
    summary: str
    confidence_score: float | None = None
    provider_confidence: float | None = None
    related_article_id: int | None = None
    related_event_id: int | None = None
    related_signal_id: int | None = None
    related_candle_id: int | None = None
    evidence_refs_json: list[dict[str, object]]
    limitations_json: list[str]


class TimelineWindowResponse(BaseModel):
    items: list[TimelineEventResponse]


class TimelineContextResponse(BaseModel):
    event: TimelineEventResponse | None
    related: list[TimelineEventResponse]
