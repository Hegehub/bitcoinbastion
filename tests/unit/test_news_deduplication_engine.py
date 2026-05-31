from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_article import NewsArticle
from app.db.models.news_source import NewsSource
from app.services.news.deduplication.deduplication_engine import DeduplicationEngine
from app.services.news.deduplication.hashing import hash_content, hash_title, hash_url, normalize_title
from app.services.news.deduplication.similarity import calculate_similarity


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def _source(db: Session) -> NewsSource:
    s = NewsSource(name="s", slug="s", kind="rss", rss_url="https://x.com/rss")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def test_tracking_param_stripping() -> None:
    assert hash_url("https://a.com/p?utm_source=x&fbclid=1") == hash_url("https://a.com/p")


def test_title_normalization_unicode() -> None:
    assert normalize_title("Bitcoin 🚀 ETF!!!") == "bitcoin etf"


def test_content_hash_stability() -> None:
    assert hash_content("<p>A   B</p>") == hash_content("A B")


def test_near_duplicate_detection() -> None:
    sim = calculate_similarity({"title": "Bitcoin ETF approval today", "canonical_url_hash": "", "content_hash": "a"}, {"title": "Today: bitcoin etf gets approval", "canonical_url_hash": "", "content_hash": "b"})
    assert sim.similarity_score > 0.5


def test_exact_url_duplicate_and_cluster() -> None:
    db = _db()
    s = _source(db)
    a1 = NewsArticle(source_id=s.id, title="A", normalized_title="a", url="https://a.com/x", raw_url="https://a.com/x", canonical_url="https://a.com/x", url_hash="", canonical_url_hash="", title_hash=hash_title("A"), normalized_title_hash="", content_hash="", author="", language="en", summary="", raw_content="", content_text="body", content_clean="body", published_at=s.created_at)
    db.add(a1)
    db.commit()
    db.refresh(a1)
    DeduplicationEngine().process_article(db, a1)
    a2 = NewsArticle(source_id=s.id, title="A2", normalized_title="a2", url="https://a.com/x?utm_source=z", raw_url="https://a.com/x?utm_source=z", canonical_url="https://a.com/x?utm_source=z", url_hash="", canonical_url_hash="", title_hash=hash_title("A2"), normalized_title_hash="", content_hash="", author="", language="en", summary="", raw_content="", content_text="body", content_clean="body", published_at=s.created_at)
    db.add(a2)
    db.commit()
    db.refresh(a2)
    DeduplicationEngine().process_article(db, a2)
    db.refresh(a2)
    assert a2.duplicate_of_id is not None
    assert a2.cluster_id is not None
    assert a2.deduplication_metadata_json.get("algorithm_version") == "dedup-v1"
