from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class AccessResource(BaseResource):
    def create_challenge(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._post("/access/challenges", json=payload, raw=raw)

    def create_session(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._post("/access/sessions", json=payload, raw=raw)

    def me(self, *, raw: bool = False) -> Any:
        return self._get("/access/me", raw=raw, require_auth=True)

    def entitlements(self, *, raw: bool = False) -> Any:
        return self._get("/access/me/entitlements", raw=raw, require_auth=True)

    def limits(self, *, raw: bool = False) -> Any:
        return self._get("/access/me/limits", raw=raw, require_auth=True)


class AsyncAccessResource(AsyncBaseResource):
    async def create_challenge(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return await self._post("/access/challenges", json=payload, raw=raw)

    async def create_session(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return await self._post("/access/sessions", json=payload, raw=raw)

    async def me(self, *, raw: bool = False) -> Any:
        return await self._get("/access/me", raw=raw, require_auth=True)

    async def entitlements(self, *, raw: bool = False) -> Any:
        return await self._get("/access/me/entitlements", raw=raw, require_auth=True)

    async def limits(self, *, raw: bool = False) -> Any:
        return await self._get("/access/me/limits", raw=raw, require_auth=True)
