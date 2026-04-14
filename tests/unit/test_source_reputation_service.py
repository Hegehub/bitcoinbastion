from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news import NewsArticle, NewsSource
from app.services.reputation.source_reputation_service import SourceReputationService


def test_refresh_source_reputation_profiles() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        source = NewsSource(name="Example", rss_url="https://example.com/rss")
        db.add(source)
        db.commit()
        db.refresh(source)
        source_id = source.id

        db.add_all(
            [
                NewsArticle(
                    source_id=source.id,
                    title="A",
                    url="https://example.com/a",
                    content_hash="h1",
                    published_at=datetime.utcnow(),
                    credibility_score=0.8,
                    impact_score=0.6,
                ),
                NewsArticle(
                    source_id=source.id,
                    title="B",
                    url="https://example.com/b",
                    content_hash="h2",
                    published_at=datetime.utcnow(),
                    credibility_score=0.7,
                    impact_score=0.5,
                ),
            ]
        )
        db.commit()

        refreshed = SourceReputationService().refresh_profiles(db=db)
        listed = SourceReputationService().list_profiles(db=db, limit=10, offset=0)

    assert len(refreshed) == 1
    assert len(listed) == 1
    assert listed[0].source_id == source_id
    assert listed[0].sample_size == 2
    assert listed[0].reliability_score > 0
