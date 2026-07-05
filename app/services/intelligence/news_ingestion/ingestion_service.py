import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news import NewsArticle, NewsSource
from app.services.intelligence.news_ingestion.article_normalizer import (
    ensure_utc,
    normalize_author,
    normalize_title,
)
from app.services.intelligence.news_ingestion.dedup_precheck import is_duplicate_candidate
from app.services.intelligence.news_ingestion.feed_parser import parse_feed
from app.services.intelligence.news_ingestion.fetch_policies import FETCH_POLICIES, FetchPolicyName
from app.services.intelligence.news_ingestion.html_cleaner import clean_html
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.intelligence.news_ingestion.metrics import (
    NEWS_ARTICLES_INGESTED_TOTAL,
    NEWS_DUPLICATE_CANDIDATES_TOTAL,
    NEWS_FETCH_TOTAL,
    NEWS_HTTP_304_TOTAL,
)
from app.services.intelligence.news_ingestion.rss_client import RSSClient
from app.services.intelligence.news_ingestion.url_canonicalizer import canonicalize_url
from app.services.market_intelligence.utils.hashing import sha256_hex

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, client: RSSClient) -> None:
        self.client = client

    def ingest_source(self, db: Session, source: NewsSource) -> dict[str, int]:
        policy = FETCH_POLICIES[FetchPolicyName.NORMAL]
        NEWS_FETCH_TOTAL.labels(source=str(source.id)).inc()
        resp = self.client.fetch(source.rss_url, policy=policy, user_agent="BitcoinBastionNews/1.0")
        if resp.status_code == 304:
            NEWS_HTTP_304_TOTAL.labels(source=str(source.id)).inc()
            return {"discovered": 0, "inserted": 0}
        items = parse_feed(resp.body)
        inserted = 0
        inserted_articles: list[NewsArticle] = []
        for item in items:
            raw_url = str(item["url"])
            canonical = canonicalize_url(raw_url)
            normalized_title = normalize_title(str(item["title"]))
            content = clean_html(str(item["summary"]))
            can_hash = sha256_hex(canonical)
            title_hash = sha256_hex(normalized_title)
            content_hash = sha256_hex(content.lower())
            existing_can = (
                db.execute(
                    select(NewsArticle.id).where(NewsArticle.canonical_url_hash == can_hash)
                ).first()
                is not None
            )
            existing_content = (
                db.execute(
                    select(NewsArticle.id).where(NewsArticle.content_hash == content_hash)
                ).first()
                is not None
            )
            existing_title = (
                db.execute(
                    select(NewsArticle.id).where(NewsArticle.title_hash == title_hash)
                ).first()
                is not None
            )
            dup, reason = is_duplicate_candidate(
                existing_canonical=existing_can,
                existing_content=existing_content,
                existing_title=existing_title,
            )
            if dup:
                NEWS_DUPLICATE_CANDIDATES_TOTAL.labels(source=str(source.id)).inc()
            article = NewsArticle(
                source_id=source.id,
                title=str(item["title"]),
                normalized_title=normalized_title,
                url=raw_url,
                canonical_url=canonical,
                url_hash=sha256_hex(raw_url),
                canonical_url_hash=can_hash,
                title_hash=title_hash,
                content_hash=content_hash,
                author=normalize_author(str(item["author"])),
                language="en",
                summary=str(item["summary"]),
                raw_content=str(item["summary"]),
                content_clean=content,
                content_text=content,
                published_at=ensure_utc(None),
                fetched_at=datetime.now(UTC),
                discovered_at=datetime.now(UTC),
                article_type="NEWS",
                ingestion_method="RSS",
                provider_confidence=source.default_confidence,
                fetch_status="fetched",
                is_duplicate_candidate=dup,
                duplicate_candidate_reason=reason,
                metadata_json={"etag": resp.etag, "last_modified": resp.last_modified},
            )
            db.add(article)
            inserted_articles.append(article)
            inserted += 1
        db.commit()
        for article in inserted_articles:
            publish_domain_event(
                db,
                "news.article.created",
                {
                    "article_id": article.id,
                    "source_name": source.name,
                    "source_type": source.kind,
                    "published_at": (
                        article.published_at.isoformat() if article.published_at else None
                    ),
                    "score": None,
                    "impact_band": "unknown",
                    "confidence": article.provider_confidence,
                    "narratives": [],
                    "limitations": ["News article ingestion records public-source metadata only."],
                },
                aggregate_type="news_article",
                aggregate_id=article.id,
                source="news_ingestion",
                idempotency_key=f"news.article.created:news_article:{article.id}:created",
            )
        NEWS_ARTICLES_INGESTED_TOTAL.labels(source=str(source.id)).inc(inserted)
        logger.info(
            "news source ingested",
            extra={
                "source_id": source.id,
                "items_discovered": len(items),
                "items_inserted": inserted,
            },
        )
        return {"discovered": len(items), "inserted": inserted}
