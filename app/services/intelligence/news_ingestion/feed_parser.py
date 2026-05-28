from datetime import UTC, datetime

import feedparser


def parse_feed(payload: str) -> list[dict[str, object]]:
    parsed = feedparser.parse(payload)
    items: list[dict[str, object]] = []
    for e in parsed.entries:
        published = datetime.now(UTC)
        if getattr(e, "published_parsed", None):
            t = e.published_parsed
            published = datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, tzinfo=UTC)
        items.append({"title": str(getattr(e, "title", "")), "url": str(getattr(e, "link", "")), "author": str(getattr(e, "author", "")), "summary": str(getattr(e, "summary", "")), "published_at": published})
    return items
