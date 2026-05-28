from __future__ import annotations

import hashlib
from datetime import UTC, datetime


def payload_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_pair(pair: str) -> str:
    p = pair.upper().replace("-", "").replace("/", "")
    return "BTCUSD" if p in {"BTCUSD", "XBTUSD"} else p


def ensure_utc(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(UTC)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
