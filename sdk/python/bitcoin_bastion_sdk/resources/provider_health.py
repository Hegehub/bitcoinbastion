from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class ProviderHealthResource(BaseResource):
    def list(self, *, raw: bool = False) -> Any:
        return self._get("/health/providers", raw=raw)

    def get(self, provider_name: str, *, raw: bool = False) -> Any:
        providers = self.list(raw=raw)
        if raw:
            return providers
        if isinstance(providers, list):
            return next((item for item in providers if isinstance(item, dict) and item.get("name") == provider_name), None)
        return None

    def degraded(self, *, raw: bool = False) -> Any:
        return self._get("/health/degraded", raw=raw)


class AsyncProviderHealthResource(AsyncBaseResource):
    async def list(self, *, raw: bool = False) -> Any:
        return await self._get("/health/providers", raw=raw)
