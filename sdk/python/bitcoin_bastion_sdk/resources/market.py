from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class MarketResource(BaseResource):
    def dashboard(self, *, raw: bool = False) -> Any:
        return self._get("/market/btc/context", raw=raw)

    def timeline(self, *, raw: bool = False) -> Any:
        return self._get("/intelligence/timeline/latest", raw=raw)

    def time_machine(self, *, raw: bool = False) -> Any:
        return self._get("/market/btc/context", raw=raw)

    def signals(self, *, raw: bool = False) -> Any:
        return self._get("/signals/latest", raw=raw)

    def narratives(self, *, raw: bool = False) -> Any:
        return self._get("/intelligence/timeline/narratives/current", raw=raw)

    def sources(self, *, raw: bool = False) -> Any:
        return self._get("/news/sources", raw=raw)

    def provider_health(self, *, raw: bool = False) -> Any:
        return self._get("/market/providers/health", raw=raw)

    def candle_evidence(self, candle_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/market/btc/candles/{candle_id}/evidence", raw=raw)


class AsyncMarketResource(AsyncBaseResource):
    async def dashboard(self, *, raw: bool = False) -> Any:
        return await self._get("/market/btc/context", raw=raw)

    async def timeline(self, *, raw: bool = False) -> Any:
        return await self._get("/intelligence/timeline/latest", raw=raw)
