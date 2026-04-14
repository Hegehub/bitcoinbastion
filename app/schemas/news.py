from datetime import datetime

from pydantic import BaseModel, HttpUrl


class NewsArticleIn(BaseModel):
    source_id: int
    title: str
    url: HttpUrl
    author: str = ""
    content_raw: str = ""
    content_clean: str = ""
    published_at: datetime
    language: str = "en"


class NewsArticleOut(BaseModel):
    id: int
    title: str
    url: str
    summary: str
    btc_relevance_score: float
    urgency_score: float
    impact_score: float
    confidence_score: float

    model_config = {"from_attributes": True}


class SourceReputationProfileOut(BaseModel):
    source_id: int
    reliability_score: float
    consistency_score: float
    signal_quality_score: float
    sample_size: int
    updated_at: datetime

    model_config = {"from_attributes": True}
