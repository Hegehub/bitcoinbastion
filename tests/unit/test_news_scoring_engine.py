from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_article import NewsArticle
from app.db.models.news_source import NewsSource
from app.services.intelligence.news_scoring.keyword_engine import score_keywords
from app.services.intelligence.news_scoring.scoring_engine import NewsScoringEngine


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_keyword_scoring_positive() -> None:
    score = score_keywords("Bitcoin ETF approval", "large inflow", "institutional adoption", {"etf", "approval", "inflow"})
    assert score > 0.5


def test_article_scoring_sets_expected_fields() -> None:
    db = _db()
    source = NewsSource(name="Test", slug="test-source", kind="RSS", base_url="https://example.com", category="general", tier="MARKET_MEDIA")
    db.add(source)
    db.flush()
    article = NewsArticle(
        source_id=source.id,
        title="Bitcoin ETF approval sparks inflow",
        normalized_title="bitcoin etf approval sparks inflow",
        raw_url="https://example.com/a",
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        url_hash="u1",
        canonical_url_hash="c1",
        title_hash="t1",
        content_hash="h1",
        published_at=datetime.utcnow(),
    )
    db.add(article)
    db.flush()
    score = NewsScoringEngine().score_article(db, article)
    assert score.btc_relevance_score >= 0
    assert score.market_impact_score >= 0
    assert "limitations" in score.limitations_json
