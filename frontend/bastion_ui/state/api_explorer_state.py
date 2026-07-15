from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.api_explorer_client import ApiExplorerApiClient


class ApiExplorerState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    degraded: bool = False
    last_updated: str = "Not available"

    async def try_public_status(self) -> None:
        self.loading = True
        result = await ApiExplorerApiClient().try_safe_read("/api/v1/public/status")
        self.data = result.data if isinstance(result.data, dict) else {}
        self.error = result.error
        self.degraded = result.degraded or not result.ok
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
