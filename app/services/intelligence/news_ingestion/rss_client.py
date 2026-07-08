from dataclasses import dataclass

import httpx

from app.services.intelligence.news_ingestion.exceptions import (
    NonRetryableFetchError,
    RetryableFetchError,
)
from app.services.intelligence.news_ingestion.fetch_policies import FetchPolicy
from app.services.intelligence.news_ingestion.retry_policy import is_retryable_status


@dataclass
class FetchResponse:
    status_code: int
    body: str
    etag: str
    last_modified: str
    content_type: str
    content_length: int


class RSSClient:
    def fetch(
        self,
        url: str,
        *,
        policy: FetchPolicy,
        user_agent: str,
        etag: str = "",
        last_modified: str = "",
    ) -> FetchResponse:
        headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        try:
            r = httpx.get(
                url, timeout=policy.timeout_seconds, headers=headers, follow_redirects=True
            )
        except httpx.TimeoutException as exc:
            raise RetryableFetchError("timeout") from exc
        if r.status_code == 304:
            return FetchResponse(
                304,
                "",
                r.headers.get("ETag", ""),
                r.headers.get("Last-Modified", ""),
                r.headers.get("Content-Type", ""),
                int(r.headers.get("Content-Length", "0")),
            )
        if is_retryable_status(r.status_code):
            raise RetryableFetchError(f"retryable status: {r.status_code}")
        if r.status_code >= 400:
            raise NonRetryableFetchError(f"http error: {r.status_code}")
        return FetchResponse(
            r.status_code,
            r.text,
            r.headers.get("ETag", ""),
            r.headers.get("Last-Modified", ""),
            r.headers.get("Content-Type", ""),
            len(r.content),
        )
