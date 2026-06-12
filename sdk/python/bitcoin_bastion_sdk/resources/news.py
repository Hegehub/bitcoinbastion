from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class NewsResource(BaseResource):
    def latest(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get("/news/latest", params={"limit": limit, "offset": offset}, raw=raw)

    def events(self, *, raw: bool = False) -> Any:
        return self._get("/news/events", raw=raw)

    def get_event(self, event_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/news/events/{event_id}", raw=raw)

    def article_score(self, article_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/news/{article_id}/score", raw=raw)


class AsyncNewsResource(AsyncBaseResource):
    async def latest(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return await self._get("/news/latest", params={"limit": limit, "offset": offset}, raw=raw)

    async def events(self, *, raw: bool = False) -> Any:
        return await self._get("/news/events", raw=raw)

    async def get_event(self, event_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/news/events/{event_id}", raw=raw)
