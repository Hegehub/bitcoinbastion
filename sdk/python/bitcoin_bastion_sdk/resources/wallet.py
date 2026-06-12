from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class WalletResource(BaseResource):
    def health(self, wallet_id: str, *, raw: bool = False) -> Any:
        assert_safe(wallet_id)
        return self._post("/wallet/health", json={"wallet_id": wallet_id}, raw=raw)

    def profile_health(self, wallet_profile_id: int | str, payload: dict[str, Any] | None = None, *, raw: bool = False) -> Any:
        return self._post(f"/wallet/profiles/{wallet_profile_id}/health", json=payload or {}, raw=raw)

    def profiles(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get("/wallet/profiles", params={"limit": limit, "offset": offset}, raw=raw)


class AsyncWalletResource(AsyncBaseResource):
    async def health(self, wallet_id: str, *, raw: bool = False) -> Any:
        assert_safe(wallet_id)
        return await self._post("/wallet/health", json={"wallet_id": wallet_id}, raw=raw)
