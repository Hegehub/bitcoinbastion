import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.services.news.deduplication.clustering import cluster_article
from app.services.news.deduplication.constants import (
    ALGORITHM_VERSION,
    DeduplicationStatus,
    NORMALIZATION_VERSION,
)
from app.services.news.deduplication.hashing import (
    hash_content,
    hash_title,
    hash_url,
    normalize_title,
)
from app.services.news.deduplication.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    def process_article(self, db: Session, article: NewsArticle) -> NewsArticle:
        article.normalized_title = normalize_title(article.title)
        article.normalized_title_hash = hash_title(article.title)
        article.canonical_url_hash = hash_url(article.canonical_url or article.url)
        article.url_hash = hashlib.sha256((article.url or "").encode("utf-8")).hexdigest()
        article.content_hash = hash_content(article.content_text or article.raw_content or "")

        existing = db.execute(
            select(NewsArticle).where(NewsArticle.id != article.id).limit(300)
        ).scalars()
        best = None
        for cand in existing:
            sim = calculate_similarity(
                {
                    "title": article.title,
                    "canonical_url_hash": article.canonical_url_hash,
                    "content_hash": article.content_hash,
                },
                {
                    "title": cand.title,
                    "canonical_url_hash": cand.canonical_url_hash,
                    "content_hash": cand.content_hash,
                },
            )
            if sim.is_exact_duplicate:
                article.duplicate_of_id = cand.id
                article.deduplication_status = DeduplicationStatus.EXACT_DUPLICATE.value
                article.similarity_score = sim.similarity_score
                article.deduplication_reason = ",".join(sim.reasons)
                article.deduplication_metadata_json = {
                    "algorithm_version": ALGORITHM_VERSION,
                    "normalization_version": NORMALIZATION_VERSION,
                    "matched_article_ids": [cand.id],
                }
                logger.info(
                    "duplicate detected", extra={"article_id": article.id, "match_id": cand.id}
                )
                db.commit()
                cluster_article(db, article.id)
                return article
            if best is None or sim.similarity_score > best[1]:
                best = (cand, sim.similarity_score, sim.reasons)
        if best and best[1] >= 0.8:
            article.duplicate_of_id = best[0].id
            article.deduplication_status = DeduplicationStatus.NEAR_DUPLICATE.value
            article.similarity_score = best[1]
            article.deduplication_reason = ",".join(best[2])
        else:
            article.deduplication_status = DeduplicationStatus.UNIQUE.value
            article.similarity_score = best[1] if best else 0.0
        article.deduplication_metadata_json = {
            "algorithm_version": ALGORITHM_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "matched_article_ids": [best[0].id] if best else [],
        }
        db.commit()
        cluster_article(db, article.id)
        return article
