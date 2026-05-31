from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_article import NewsArticle
from app.db.models.news_source import NewsSource
from app.services.intelligence.news_scoring.scoring_service import NewsScoringService


def test_score_security_article() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    db = Session(engine)
    src = NewsSource(name="S", slug="s", kind="RSS", base_url="https://x", category="general", tier="MARKET_MEDIA")
    db.add(src)
    db.flush()
    a = NewsArticle(source_id=src.id, title="Exchange hack exploit", normalized_title="exchange hack exploit", raw_url="u", url="u", canonical_url="u", url_hash="u1", canonical_url_hash="c1", title_hash="t1", content_hash="h1", published_at=datetime.utcnow())
    db.add(a)
    db.flush()
    scored = NewsScoringService().score_article(db, a)
    assert scored.security_risk_score > 0
    assert "limitations" in scored.limitations_json
