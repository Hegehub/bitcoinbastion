from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.provider_health_client import ProviderHealthApiClient

PROVIDER_HEALTH_ENDPOINT_MISSING = "Global provider health endpoint is not available yet."


class ConsoleProviderHealthState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    last_updated: str = "Not available"
    degraded: bool = True
    status: str = "unknown"

    async def refresh(self) -> None:
        self.loading = True
        result = await ProviderHealthApiClient().get_provider_health()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.status = str(result.data.get("status") or "unknown")
            self.error = None
            self.degraded = result.degraded or self.status in {
                "degraded",
                "stale",
                "unavailable",
                "unknown",
            }
        else:
            self.data = {
                "available": False,
                "reason": PROVIDER_HEALTH_ENDPOINT_MISSING,
                "future_endpoint": "/api/v1/provider-health",
            }
            self.status = "unknown"
            self.error = result.error
            self.degraded = True
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
