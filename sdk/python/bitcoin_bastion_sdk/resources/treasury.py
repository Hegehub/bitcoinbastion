from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class TreasuryResource(BaseResource):
    def create_request(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._post("/treasury/requests", json=payload, raw=raw, require_auth=True)

    def list_requests(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get(
            "/treasury/requests",
            params={"limit": limit, "offset": offset},
            raw=raw,
            require_auth=True,
        )

    def pending_approvals(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return self._get(
            "/treasury/requests/pending-approvals",
            params={"limit": limit, "offset": offset},
            raw=raw,
            require_auth=True,
        )

    def approve_request(
        self, request_id: int | str, payload: dict[str, Any] | None = None, *, raw: bool = False
    ) -> Any:
        return self._post(
            f"/treasury/requests/{request_id}/approve",
            json=payload or {},
            raw=raw,
            require_auth=True,
        )

    def reject_request(
        self, request_id: int | str, payload: dict[str, Any] | None = None, *, raw: bool = False
    ) -> Any:
        return self._post(
            f"/treasury/requests/{request_id}/reject",
            json=payload or {},
            raw=raw,
            require_auth=True,
        )


class AsyncTreasuryResource(AsyncBaseResource):
    async def create_request(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return await self._post("/treasury/requests", json=payload, raw=raw, require_auth=True)

    async def list_requests(self, *, limit: int = 20, offset: int = 0, raw: bool = False) -> Any:
        return await self._get(
            "/treasury/requests",
            params={"limit": limit, "offset": offset},
            raw=raw,
            require_auth=True,
        )
