from pydantic import BaseModel


class ScoreResponse(BaseModel):
    article_id: int | None = None
    event_id: int | None = None
    btc_relevance_score: float
    market_impact_score: float
    urgency_score: float
    sentiment_score: float
    confidence_score: float
    provider_confidence: float
    factor_breakdown: dict[str, object]
    explanation: dict[str, str]
    limitations: dict[str, object]
