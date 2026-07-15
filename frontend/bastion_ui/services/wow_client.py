from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.models import ApiResult

UNAVAILABLE_REASON = "Backend wow-layer data endpoint is not available yet."


class WowApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def _safe_get(self, path: str | None) -> ApiResult:
        if path is None:
            return ApiResult(ok=False, error=UNAVAILABLE_REASON, degraded=True)
        try:
            payload = await self.api_client.get(path)
            data: dict[str, Any] | list[Any] | None = (
                payload if isinstance(payload, dict | list) else None
            )
            degraded = (
                bool(payload.get("degraded") or payload.get("stale"))
                if isinstance(payload, dict)
                else False
            )
            return ApiResult(ok=True, data=data, degraded=degraded)
        except BastionApiError as exc:
            return ApiResult(
                ok=False, error=exc.public_message, status_code=exc.status_code, degraded=True
            )

    async def get_trace_radar(self, report_id: str) -> ApiResult:
        return await self._safe_get(
            f"/api/v1/public/trace/{report_id}/summary" if report_id else None
        )

    async def get_evidence_chain(self, packet_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/evidence/{packet_id}" if packet_id else None)

    async def get_provider_matrix(self) -> ApiResult:
        return await self._safe_get("/api/v1/health")

    async def get_node_pulse(self) -> ApiResult:
        return await self._safe_get("/api/v1/public/status")

    async def get_sovereignty_score(self) -> ApiResult:
        return await self._safe_get(None)

    async def get_market_wall(self) -> ApiResult:
        return await self._safe_get("/web/market-time-machine")

    async def get_audit_replay(self) -> ApiResult:
        return await self._safe_get(None)
