from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.models import ApiResult

SAFE_READ_PATHS = {
    "/api/v1/public/status",
    "/api/v1/public/roadmap",
    "/api/v1/public/features",
    "/api/v1/signals/top",
}


@dataclass(frozen=True)
class ApiExplorerEndpoint:
    method: str
    path: str
    category: str
    safety: str
    tryable: bool = False


class ApiExplorerApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    def endpoint_catalog(self) -> tuple[ApiExplorerEndpoint, ...]:
        return (
            ApiExplorerEndpoint("GET", "/api/v1/public/status", "Public", "Safe read", True),
            ApiExplorerEndpoint("GET", "/api/v1/public/roadmap", "Public", "Safe read", True),
            ApiExplorerEndpoint("GET", "/api/v1/public/features", "Public", "Safe read", True),
            ApiExplorerEndpoint("GET", "/api/v1/signals/top", "Signals", "Safe read", True),
            ApiExplorerEndpoint(
                "GET", "/api/v1/public/trace/{report_id}/summary", "Trace", "Safe read", False
            ),
            ApiExplorerEndpoint("POST", "/api/v1/treasury/drafts", "Treasury", "Draft-only", False),
            ApiExplorerEndpoint(
                "PATCH", "/api/v1/policy/rules/{rule_id}", "Policy", "Requires approval", False
            ),
            ApiExplorerEndpoint(
                "POST", "/api/v1/webhooks/secrets", "Webhooks", "Admin-only", False
            ),
        )

    async def try_safe_read(self, path: str) -> ApiResult:
        if path not in SAFE_READ_PATHS:
            return ApiResult(
                ok=False,
                error="Only safe read endpoints can be tried from the Reflex API Explorer.",
                degraded=True,
            )
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
