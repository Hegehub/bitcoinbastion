from datetime import datetime, timedelta

from app.db.models.news_article import NewsArticle
from app.services.news_scoring.scoring_service import NewsScoringService


def _article(title: str, summary: str = "", content: str = "") -> NewsArticle:
    return NewsArticle(
        id=1,
        source_id=1,
        title=title,
        normalized_title=title.lower(),
        raw_url="u",
        url="u",
        canonical_url="u",
        url_hash="h",
        canonical_url_hash="ch",
        title_hash="th",
        content_hash="co",
        summary=summary,
        content_text=content,
        provider_confidence=0.8,
        published_at=datetime.utcnow(),
    )


def test_positive_institutional_etf_news() -> None:
    s = NewsScoringService()
    score = s.score_article(_article("BlackRock ETF approval and inflow"))
    assert score.institutional_score > 0
    assert score.sentiment_label in {"POSITIVE", "MIXED"}


def test_negative_security_hack_news() -> None:
    s = NewsScoringService()
    score = s.score_article(_article("Exchange hack exploit breach alert"))
    assert score.security_risk_score > 0
    assert score.risk_band in {"HIGH", "CRITICAL", "MEDIUM"}


def test_deterministic_scoring() -> None:
    s = NewsScoringService()
    a = _article("Fed rates and bitcoin liquidity")
    one = s.score_article(a)
    two = s.score_article(a)
    assert one.factor_breakdown_json == two.factor_breakdown_json


def test_low_confidence_article() -> None:
    s = NewsScoringService()
    a = _article("random lifestyle update")
    a.provider_confidence = 0.1
    a.published_at = datetime.utcnow() - timedelta(days=5)
    out = s.score_article(a)
    assert out.confidence_score < 0.5
