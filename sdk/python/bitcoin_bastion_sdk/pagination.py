from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol


class _ListCallable(Protocol):
    def __call__(self, *, limit: int, offset: int) -> dict[str, Any]: ...


def iter_paginated(fetch: _ListCallable, *, limit: int = 100) -> Iterator[dict[str, Any]]:
    offset = 0
    while True:
        page = fetch(limit=limit, offset=offset)
        items = page.get("items", []) if isinstance(page, dict) else []
        if not isinstance(items, list) or not items:
            return
        for item in items:
            if isinstance(item, dict):
                yield item
        if len(items) < limit:
            return
        offset += limit
