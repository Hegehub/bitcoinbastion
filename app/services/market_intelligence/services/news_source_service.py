import logging

logger = logging.getLogger(__name__)


class NewsSourceService:
    def create_source(self, payload: object) -> object:
        logger.info("source created", extra={"event": "source_created"})
        raise NotImplementedError

    def update_source(self, source_id: int, payload: object) -> object:
        raise NotImplementedError

    def disable_source(self, source_id: int) -> None:
        logger.info("source disabled", extra={"event": "source_disabled", "source_id": source_id})
        raise NotImplementedError

    def get_active_sources(self) -> list[object]:
        raise NotImplementedError
