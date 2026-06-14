from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class OnchainResource(BaseResource):
    def events(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get("/onchain/events", params={"limit": limit, "offset": offset}, raw=raw)

    def state(self, *, raw: bool = False) -> Any:
        return self._get("/onchain/state", raw=raw)


class AsyncOnchainResource(AsyncBaseResource):
    async def events(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return await self._get("/onchain/events", params={"limit": limit, "offset": offset}, raw=raw)

    async def state(self, *, raw: bool = False) -> Any:
        return await self._get("/onchain/state", raw=raw)
