from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.models import ApiResult

POLICY_ENDPOINT = "/api/v1/policy"


class PolicyApiClient:
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
                ok=False, error=exc.public_message, status_code=exc.status_code, degraded=True
            )

    async def get_policy_facts(self, report_id: str) -> ApiResult:
        return await self._safe_get(f"/api/v1/trace/report/{report_id}/policy-facts")

    async def get_policy_baseline(self) -> ApiResult:
        return await self._safe_get(POLICY_ENDPOINT)
