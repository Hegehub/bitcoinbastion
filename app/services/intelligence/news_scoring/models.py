from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsScoreBreakdown:
    article_id: int
    btc_relevance_score: float
    market_impact_score: float
    urgency_score: float
    sentiment_score: float
    sentiment_label: str
    source_credibility_score: float
    institutional_score: float
    macro_score: float
    regulatory_score: float
    security_risk_score: float
    sovereignty_score: float
    confidence_score: float
    factor_contributions_json: dict[str, object]
    keywords_detected_json: dict[str, object]
    categories_detected_json: dict[str, object]
    limitations_json: dict[str, object]
    generated_at: datetime
