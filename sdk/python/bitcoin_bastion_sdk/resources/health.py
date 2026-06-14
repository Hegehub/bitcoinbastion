from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class HealthResource(BaseResource):
    def health(self, *, raw: bool = False) -> Any:
        return self._get("/health", raw=raw)

    def ready(self, *, raw: bool = False) -> Any:
        return self._get("/health/ready", raw=raw)

    def runtime(self, *, raw: bool = False) -> Any:
        return self._get("/health/runtime", raw=raw)

    def public_status(self, *, raw: bool = False) -> Any:
        return self._get("/public/status", raw=raw)

    def operations_status(self, *, raw: bool = False) -> Any:
        return self._get("/operations/status", raw=raw)


class AsyncHealthResource(AsyncBaseResource):
    async def health(self, *, raw: bool = False) -> Any:
        return await self._get("/health", raw=raw)

    async def ready(self, *, raw: bool = False) -> Any:
        return await self._get("/health/ready", raw=raw)
