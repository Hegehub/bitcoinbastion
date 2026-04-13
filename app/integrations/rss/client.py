from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser


@dataclass
class RSSItem:
    title: str
    url: str
    author: str
    content: str
    published_at: datetime | None


class RSSClient:
    def fetch(self, rss_url: str) -> list[RSSItem]:
        feed = feedparser.parse(rss_url)
        items: list[RSSItem] = []
        for entry in feed.entries:
            content = ""
            if hasattr(entry, "summary"):
                content = str(entry.summary)
            published = datetime.now(UTC)
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=UTC)
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
