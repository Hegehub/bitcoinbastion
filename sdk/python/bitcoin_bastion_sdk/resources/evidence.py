from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource


class EvidenceResource(BaseResource):
    def list_packets(self, *, raw: bool = False) -> Any:
        return self._get("/evidence/packets", raw=raw)

    def get_packet(self, packet_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/evidence/packets/{packet_id}", raw=raw)

    def get_replay(self, entity_type: str, entity_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/evidence/replay/{entity_type}/{entity_id}", raw=raw)

    def market_memory(self, event_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/evidence/market-memory/{event_id}", raw=raw)


class AsyncEvidenceResource(AsyncBaseResource):
    async def list_packets(self, *, raw: bool = False) -> Any:
        return await self._get("/evidence/packets", raw=raw)

    async def get_packet(self, packet_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/evidence/packets/{packet_id}", raw=raw)
