from sqlalchemy.orm import Session

from app.db.models.news_source import NewsSource
from app.services.intelligence.news_ingestion.feed_parser import parse_feed
from app.services.intelligence.news_ingestion.rss_client import RSSClient
from app.services.news.provider_confidence_service import (
    HealthResult,
    ProviderConfidenceService,
    SourceFailureType,
)


class SourceHealthService:
    def __init__(self) -> None:
        self.client = RSSClient()
        self.conf = ProviderConfidenceService()

    def check_source(self, db: Session, source: NewsSource) -> None:
        try:
            resp = self.client.fetch(
                source.rss_url,
                policy=type("P", (), {"timeout_seconds": 10})(),
                user_agent="BitcoinBastionHealth/1.0",
                etag=source.etag or "",
                last_modified=source.last_modified or "",
            )
            if resp.status_code == 304:
                res = HealthResult(
                    success=True,
                    status_code=304,
                    latency_ms=0,
                    response_size_bytes=0,
                    etag=resp.etag,
                    last_modified=resp.last_modified,
                )
            elif not resp.body.strip():
                res = HealthResult(
                    success=False,
                    status_code=resp.status_code,
                    latency_ms=0,
                    failure_type=SourceFailureType.EMPTY_RESPONSE,
                    error_message="empty response",
                )
            else:
                parse_feed(resp.body)
                res = HealthResult(
                    success=True,
                    status_code=resp.status_code,
                    latency_ms=0,
                    response_size_bytes=resp.content_length,
                    etag=resp.etag,
                    last_modified=resp.last_modified,
                )
        except Exception as exc:
            res = HealthResult(
                success=False,
                status_code=None,
                latency_ms=None,
                failure_type=SourceFailureType.UNKNOWN,
                error_message=str(exc),
            )
        self.conf.apply_health_result(db, source, res)
