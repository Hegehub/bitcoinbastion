from app.services.intelligence.news_scoring.sentiment_engine import SentimentEngine


def test_positive_sentiment() -> None:
    score, label, _ = SentimentEngine().analyze("ETF approval and adoption inflow")
    assert label in {"POSITIVE", "MIXED"}
    assert score >= 0.5
