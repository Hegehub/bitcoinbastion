from __future__ import annotations

from bastion_ui.services.market_client import MarketApiClient
from bastion_ui.services.models import ApiResult


class TimeMachineApiClient:
    def __init__(self, market_client: MarketApiClient | None = None) -> None:
        self.market_client = market_client or MarketApiClient()

    async def get_time_machine(self) -> ApiResult:
        return await self.market_client.get_time_machine()

    async def get_timeline(self) -> ApiResult:
        return await self.market_client.get_timeline()

    async def get_candle_detail(self, candle_id: str) -> ApiResult:
        return await self.market_client.get_candle_detail(candle_id)

    async def get_evidence_packet(self, packet_id: str) -> ApiResult:
        return await self.market_client.get_evidence_packet(packet_id)
