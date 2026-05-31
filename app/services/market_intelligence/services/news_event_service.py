import logging

logger = logging.getLogger(__name__)


class NewsEventService:
    def create_event(self, payload: object) -> object:
        logger.info("event created", extra={"event": "event_created"})
        raise NotImplementedError

    def attach_article(self, event_id: int, article_id: int) -> object:
        raise NotImplementedError

    def get_recent_events(self, limit: int = 20) -> list[object]:
        raise NotImplementedError
