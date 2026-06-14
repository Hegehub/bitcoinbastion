from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class PolicyResource(BaseResource):
    def evaluate(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._post("/policy/check", json=payload, raw=raw)

    def list_profiles(self, *, raw: bool = False) -> Any:
        return self._get("/policy/catalog", raw=raw)

    def executions(self, *, raw: bool = False) -> Any:
        return self._get("/policy/executions", raw=raw)


class AsyncPolicyResource(AsyncBaseResource):
    async def evaluate(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return await self._post("/policy/check", json=payload, raw=raw)

    async def list_profiles(self, *, raw: bool = False) -> Any:
        return await self._get("/policy/catalog", raw=raw)
