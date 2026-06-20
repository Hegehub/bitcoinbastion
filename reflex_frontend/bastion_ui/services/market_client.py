from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient


class MarketApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_market_dashboard(self) -> Any:
        return await self.api_client.get("/api/v1/market/health")

    async def get_market_time_machine(self) -> Any:
        return await self.api_client.get("/web/market-time-machine")

    async def get_timeline(self) -> Any:
        return await self.api_client.get("/web/timeline")

    async def get_candle(self, candle_id: str) -> Any:
        return await self.api_client.get(f"/web/candle/{candle_id}")

    async def get_evidence(self, packet_id: str) -> Any:
        return await self.api_client.get(f"/web/evidence/{packet_id}")
