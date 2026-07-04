import logging

logger = logging.getLogger(__name__)


class NewsArticleService:
    def create_article(self, payload: object) -> object:
        logger.info("article created", extra={"event": "article_created"})
        raise NotImplementedError

    def mark_duplicate(self, article_id: int, duplicate_of_id: int) -> object:
        logger.info(
            "duplicate marked", extra={"event": "duplicate_marked", "article_id": article_id}
        )
        raise NotImplementedError

    def get_recent_articles(self, limit: int = 20) -> list[object]:
        raise NotImplementedError
