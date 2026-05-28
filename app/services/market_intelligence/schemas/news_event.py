from datetime import datetime

from pydantic import BaseModel


class CreateNewsEventRequest(BaseModel):
    event_type: str
    canonical_title: str


class NewsEventArticleResponse(BaseModel):
    article_id: int
    relationship_type: str
    similarity_score: float | None = None
    is_primary_source: bool = False
    time_distance_seconds: int | None = None


class NewsEventClusterResponse(BaseModel):
    id: int
    cluster_hash: str
    cluster_strategy: str
    cluster_reason: str
    candidate_count: int
    accepted_count: int
    rejected_count: int
    confidence_score: float


class NewsEventResponse(BaseModel):
    id: int
    event_type: str
    event_category: str
    canonical_title: str
    canonical_summary: str
    source_count: int
    article_count: int
    event_confidence: float
    first_seen_at: datetime
    last_seen_at: datetime
