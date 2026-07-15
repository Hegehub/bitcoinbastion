from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient


class StatusApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_public_status(self) -> Any:
        return await self.api_client.get("/api/v1/public/status")

    async def get_provider_health(self) -> Any:
        return await self.api_client.get("/api/v1/health/providers")

    async def get_health(self) -> Any:
        return await self.api_client.get("/api/v1/health")
