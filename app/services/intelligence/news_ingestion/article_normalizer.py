from datetime import UTC, datetime


def normalize_title(title: str) -> str:
    return " ".join(title.split()).strip().lower()


def normalize_author(author: str) -> str:
    return " ".join(author.split()).strip()


def ensure_utc(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(UTC)
    return ts.astimezone(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
