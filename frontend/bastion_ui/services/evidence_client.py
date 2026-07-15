from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import (
    NOT_FOUND_PUBLIC_MESSAGE,
    BastionApiError,
    BastionApiNotFoundError,
)
from bastion_ui.services.models import ApiResult


class EvidenceApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def _safe_get(self, path: str) -> ApiResult:
        try:
            payload = await self.api_client.get(path)
            data: dict[str, Any] | list[Any] | None
            data = payload if isinstance(payload, dict | list) else None
            degraded = bool(payload.get("degraded")) if isinstance(payload, dict) else False
            return ApiResult(ok=True, data=data, degraded=degraded)
        except BastionApiError as exc:
            return ApiResult(
                ok=False,
                error=exc.public_message,
                status_code=exc.status_code,
                degraded=True,
            )

    async def get_trace_evidence(self, report_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/trace/report/{report_id}/evidence")

    async def get_proof_packet(self, report_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/trace/report/{report_id}/proof-packet")

    async def get_provider_disagreement(self, report_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/trace/report/{report_id}/provider-disagreement")

    async def get_public_trace_summary(self, report_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/public/trace/{report_id}/summary")

    async def get_evidence_packet(self, packet_id: str) -> ApiResult:
        return await self._safe_get(f"/web/evidence/{packet_id}")

    async def get_trace_report_evidence(self, report_id: str) -> ApiResult:
        return await self.get_trace_evidence(report_id)

    async def get_json_evidence_packet(self, packet_id: str) -> Any:
        raise BastionApiNotFoundError(
            f"No stable JSON evidence endpoint is documented for packet {packet_id}.",
            public_message=NOT_FOUND_PUBLIC_MESSAGE,
            status_code=404,
        )
