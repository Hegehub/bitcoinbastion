from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNCERTAIN = "UNCERTAIN"


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ScoringMethod(str, Enum):
    RULE_BASED = "RULE_BASED"
    LOCAL_MODEL = "LOCAL_MODEL"
    HYBRID = "HYBRID"


class NewsArticleScoreResponse(BaseModel):
    article_id: int
    event_id: int | None = None
    sentiment_label: SentimentLabel
    risk_band: RiskBand
    confidence_score: float
    score_version: str
    scoring_method: ScoringMethod
    factor_breakdown_json: dict[str, object]
    limitations_json: dict[str, object]
    created_at: datetime | None = None
