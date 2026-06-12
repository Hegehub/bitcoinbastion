from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class WebhooksResource(BaseResource):
    def create(
        self,
        *,
        url: str,
        events: list[str],
        name: str = "Bitcoin Bastion webhook",
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        raw: bool = False,
    ) -> Any:
        payload = {"name": name, "target_url": url, "description": description, "event_types": events, "metadata": metadata}
        assert_safe(payload)
        return self._post("/webhooks", json=payload, raw=raw)

    def list(self, *, limit: int = 50, offset: int = 0, raw: bool = False) -> Any:
        return self._get("/webhooks", params={"limit": limit, "offset": offset}, raw=raw)

    def get(self, webhook_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/webhooks/{webhook_id}", raw=raw)

    def update(self, webhook_id: int | str, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._patch(f"/webhooks/{webhook_id}", json=payload, raw=raw)

    def delete(self, webhook_id: int | str, *, raw: bool = False) -> Any:
        return self._delete(f"/webhooks/{webhook_id}", raw=raw)

    def test(self, webhook_id: int | str, payload: dict[str, Any] | None = None, *, raw: bool = False) -> Any:
        if payload is not None:
            assert_safe(payload)
        return self._post(f"/webhooks/{webhook_id}/test", json=payload or {}, raw=raw)

    def deliveries(self, webhook_id: int | str, *, limit: int = 50, offset: int = 0, raw: bool = False) -> Any:
        return self._get(f"/webhooks/{webhook_id}/deliveries", params={"limit": limit, "offset": offset}, raw=raw)


class AsyncWebhooksResource(AsyncBaseResource):
    async def list(self, *, limit: int = 50, offset: int = 0, raw: bool = False) -> Any:
        return await self._get("/webhooks", params={"limit": limit, "offset": offset}, raw=raw)
