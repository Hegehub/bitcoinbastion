from pydantic import BaseModel


class SentimentResponse(BaseModel):
    sentiment_label: str
    sentiment_score: float
    matched_keywords: list[str]
    reasoning: list[str]
