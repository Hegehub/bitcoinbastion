from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_article import NewsArticle
from app.db.models.news_source import NewsSource
from app.services.intelligence.news_price_impact_service import NewsPriceImpactService


def test_price_impact_article_calc() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    db = Session(engine)
    src = NewsSource(
        name="S",
        slug="s",
        kind="RSS",
        base_url="https://x",
        category="general",
        tier="MARKET_MEDIA",
    )
    db.add(src)
    db.flush()
    a = NewsArticle(
        source_id=src.id,
        title="ETF approval inflow",
        normalized_title="etf approval inflow",
        raw_url="u",
        url="u",
        canonical_url="u",
        url_hash="u1",
        canonical_url_hash="c1",
        title_hash="t1",
        content_hash="h1",
        published_at=datetime.utcnow(),
        market_impact_score=0.8,
        btc_relevance_score=0.9,
    )
    db.add(a)
    db.flush()
    row = NewsPriceImpactService().calculate_for_article(db, a.id)
    assert row is not None
    assert 0.0 <= row.confidence_score <= 1.0
