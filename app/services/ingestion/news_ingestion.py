import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models.news import NewsArticle, NewsSource
from app.db.repositories.news_repository import NewsRepository
from app.integrations.rss.client import RSSClient, RSSItem


@dataclass
class IngestionResult:
    inserted: int
    duplicates: int


class NewsIngestionService:
    def __init__(self, rss_client: RSSClient) -> None:
        self.rss_client = rss_client

    @staticmethod
    def normalize_text(value: str) -> str:
        return " ".join(value.split()).strip()

    @staticmethod
    def content_hash(title: str, url: str) -> str:
        material = f"{title.lower()}::{url.lower()}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def ingest_source(self, source: NewsSource, repo: NewsRepository) -> IngestionResult:
        inserted = 0
        duplicates = 0

        items = self.rss_client.fetch(source.rss_url)
        for item in items:
            article_hash = self.content_hash(item.title, item.url)
            existing = repo.get_by_hash(article_hash)
            if existing is not None:
                duplicates += 1
                continue

            article = self._item_to_model(source.id, item, article_hash)
            repo.add(article)
            inserted += 1

        return IngestionResult(inserted=inserted, duplicates=duplicates)

    def _item_to_model(self, source_id: int, item: RSSItem, article_hash: str) -> NewsArticle:
        return NewsArticle(
            source_id=source_id,
            title=self.normalize_text(item.title),
            url=item.url,
            author=item.author,
            content_raw=item.content,
            content_clean=self.normalize_text(item.content),
            published_at=item.published_at or datetime.now(UTC),
            fetched_at=datetime.now(UTC),
            content_hash=article_hash,
        )
