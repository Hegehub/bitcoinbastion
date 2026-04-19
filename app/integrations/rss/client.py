from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class RSSItem:
    title: str
    url: str
    author: str
    content: str
    published_at: datetime | None


class RSSClient:
    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def _fetch_raw(self, rss_url: str) -> str:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(rss_url)
            response.raise_for_status()
            return response.text

    def fetch(self, rss_url: str) -> list[RSSItem]:
        raw_xml = self._fetch_raw(rss_url)
        feed = feedparser.parse(raw_xml)
        items: list[RSSItem] = []
        for entry in feed.entries:
            content = ""
            if hasattr(entry, "summary"):
                content = str(entry.summary)
            published = datetime.now(UTC)
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                year = int(entry.published_parsed.tm_year)
                month = int(entry.published_parsed.tm_mon)
                day = int(entry.published_parsed.tm_mday)
                hour = int(entry.published_parsed.tm_hour)
                minute = int(entry.published_parsed.tm_min)
                second = int(entry.published_parsed.tm_sec)
                published = datetime(
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    tzinfo=UTC,
                )
            items.append(
                RSSItem(
                    title=str(getattr(entry, "title", "")),
                    url=str(getattr(entry, "link", "")),
                    author=str(getattr(entry, "author", "")),
                    content=content,
                    published_at=published,
                )
            )
        return items
