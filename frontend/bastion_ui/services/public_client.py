from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient


class PublicApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_landing(self) -> Any:
        return await self.api_client.get("/api/v1/public/landing")

    async def get_status(self) -> Any:
        return await self.api_client.get("/api/v1/public/status")

    async def get_roadmap(self) -> Any:
        return await self.api_client.get("/api/v1/public/roadmap")

    async def get_stats(self) -> Any:
        return await self.api_client.get("/api/v1/public/stats")

    async def get_features(self) -> Any:
        return await self.api_client.get("/api/v1/public/features")

    async def get_public_trace_summary(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/public/trace/{report_id}/summary")


async def get_landing() -> Any:
    return await PublicApiClient().get_landing()


async def get_status() -> Any:
    return await PublicApiClient().get_status()


async def get_roadmap() -> Any:
    return await PublicApiClient().get_roadmap()


async def get_stats() -> Any:
    return await PublicApiClient().get_stats()


async def get_features() -> Any:
    return await PublicApiClient().get_features()


async def get_public_trace_summary(report_id: str) -> Any:
    return await PublicApiClient().get_public_trace_summary(report_id)
