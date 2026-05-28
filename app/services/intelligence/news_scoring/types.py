from typing import TypedDict


class SentimentResult(TypedDict):
    sentiment_label: str
    sentiment_score: float
    matched_keywords: list[str]
    reasoning: list[str]
