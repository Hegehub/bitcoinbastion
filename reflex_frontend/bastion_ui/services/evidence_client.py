from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import NOT_FOUND_PUBLIC_MESSAGE, BastionApiNotFoundError


class EvidenceApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_evidence_packet(self, packet_id: str) -> Any:
        return await self.api_client.get(f"/web/evidence/{packet_id}")

    async def get_trace_report_evidence(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/evidence")

    async def get_json_evidence_packet(self, packet_id: str) -> Any:
        raise BastionApiNotFoundError(
            f"No stable JSON evidence endpoint is documented for packet {packet_id}.",
            public_message=NOT_FOUND_PUBLIC_MESSAGE,
            status_code=404,
        )
