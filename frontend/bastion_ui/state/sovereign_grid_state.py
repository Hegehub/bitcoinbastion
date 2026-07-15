from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.sovereign_grid_client import SovereignGridApiClient

SOVEREIGN_GRID_MISSING = "Sovereign Grid backend readiness endpoint is pending."


class SovereignGridState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    degraded: bool = True
    last_updated: str = "Not available"
    status: str = "unknown"

    async def refresh(self) -> None:
        self.loading = True
        result = await SovereignGridApiClient().get_public_status()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.status = str(result.data.get("status") or "unknown")
            self.error = None
            self.degraded = result.degraded or self.status == "unknown"
        else:
            self.data = {"available": False, "reason": SOVEREIGN_GRID_MISSING}
            self.status = "unknown"
            self.error = result.error
            self.degraded = True
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
