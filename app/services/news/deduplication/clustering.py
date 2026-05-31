from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.db.models.news_article_cluster import NewsArticleCluster
from app.services.news.deduplication.constants import DeduplicationStatus
from app.services.news.deduplication.similarity import calculate_similarity


def find_cluster_candidates(db: Session, article: NewsArticle) -> list[NewsArticle]:
    recent = datetime.now(UTC) - timedelta(days=2)
    stmt = select(NewsArticle).where(NewsArticle.id != article.id, NewsArticle.published_at >= recent)
    return list(db.execute(stmt).scalars())


def cluster_article(db: Session, article_id: int) -> int | None:
    article = db.get(NewsArticle, article_id)
    if article is None:
        return None
    candidates = find_cluster_candidates(db, article)
    best: NewsArticle | None = None
    best_score = 0.0
    for c in candidates:
        sim = calculate_similarity({"title": article.title, "canonical_url_hash": article.canonical_url_hash, "content_hash": article.content_hash}, {"title": c.title, "canonical_url_hash": c.canonical_url_hash, "content_hash": c.content_hash})
        if sim.similarity_score > best_score:
            best_score = sim.similarity_score
            best = c
    if best is None or best_score < 0.75:
        cl = NewsArticleCluster(cluster_key=f"cl-{article.id}", canonical_article_id=article.id, cluster_type="topic", article_count=1, first_seen_at=article.published_at, last_seen_at=article.published_at, cluster_confidence=1.0, cluster_summary=article.title)
        db.add(cl)
        db.flush()
        article.cluster_id = cl.id
        article.is_canonical = True
        article.deduplication_status = DeduplicationStatus.CANONICAL.value
    else:
        article.cluster_id = best.cluster_id
        article.deduplication_status = DeduplicationStatus.CLUSTERED.value
    db.commit()
    return article.cluster_id


def recluster_recent_articles(db: Session) -> int:
    ids = [x for x, in db.execute(select(NewsArticle.id).where(NewsArticle.cluster_id.is_(None)).limit(200)).all()]
    for aid in ids:
        cluster_article(db, aid)
    return len(ids)
