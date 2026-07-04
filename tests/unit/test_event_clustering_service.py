from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_article import NewsArticle
from app.db.models.news_source import NewsSource
from app.services.intelligence.event_clustering_service import CanonicalNewsEventService


def _source() -> NewsSource:
    return NewsSource(
        name="S",
        slug="s",
        kind="rss",
        base_url="https://x",
        rss_url="https://x/feed",
        category="bitcoin_media",
        tier="bitcoin_native",
        language="en",
        country_code="US",
    )


def _article(source_id: int, title: str, ntitle: str, hours: int = 0) -> NewsArticle:
    now = datetime.utcnow() - timedelta(hours=hours)
    return NewsArticle(
        source_id=source_id,
        external_id="",
        title=title,
        normalized_title=ntitle,
        raw_url=f"https://x/{source_id}/{abs(hash(title))}",
        url=f"https://x/{source_id}/{abs(hash(title))}",
        canonical_url=f"https://x/{source_id}/{abs(hash(title))}",
        url_hash=f"{abs(hash(title))}1",
        canonical_url_hash=f"{abs(hash(title))}2",
        title_hash=f"{abs(hash(title))}3",
        content_hash=f"{abs(hash(title))}4",
        published_at=now,
    )


def test_cluster_related_etf_articles() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db_session:
        s = _source()
        db_session.add(s)
        db_session.flush()
        a1 = _article(s.id, "BlackRock ETF inflows surge", "blackrock etf inflows surge")
        a2 = _article(s.id, "BlackRock ETF inflows jump", "blackrock etf inflows jump", 1)
        db_session.add_all([a1, a2])
        db_session.commit()

        svc = CanonicalNewsEventService()
        e1 = svc.cluster_article(db_session, a1.id)
        e2 = svc.cluster_article(db_session, a2.id)
        db_session.commit()

        assert e1 is not None and e2 is not None
        assert e1.id == e2.id
