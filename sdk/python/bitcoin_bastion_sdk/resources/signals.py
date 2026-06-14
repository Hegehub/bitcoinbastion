from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from bitcoin_bastion_sdk.pagination import iter_paginated
from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class SignalsResource(BaseResource):
    def list_top(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get("/signals/top", params={"limit": limit, "offset": offset}, raw=raw)

    def iter_top(self, *, limit: int = 100) -> Iterator[dict[str, Any]]:
        yield from iter_paginated(lambda *, limit, offset: self.list_top(limit=limit, offset=offset), limit=limit)

    def latest(self, *, raw: bool = False) -> Any:
        return self._get("/signals/latest", raw=raw)

    def get(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/signals/{signal_id}", raw=raw)

    def get_evidence(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/signals/{signal_id}/evidence", raw=raw)

    def get_delivery_logs(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/signals/{signal_id}/delivery-logs", raw=raw)

    def recommendations(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/signals/{signal_id}/recommendations", raw=raw)

    def explanation(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/signals/{signal_id}/explanation", raw=raw)


class AsyncSignalsResource(AsyncBaseResource):
    async def list_top(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return await self._get("/signals/top", params={"limit": limit, "offset": offset}, raw=raw)

    async def latest(self, *, raw: bool = False) -> Any:
        return await self._get("/signals/latest", raw=raw)

    async def get(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/signals/{signal_id}", raw=raw)

    async def get_evidence(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/signals/{signal_id}/evidence", raw=raw)

    async def get_delivery_logs(self, signal_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/signals/{signal_id}/delivery-logs", raw=raw)
