from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.time_machine_client import TimeMachineApiClient

TIME_MACHINE_MISSING = "No Time Machine data available yet."


class TimeMachineState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    degraded: bool = True
    last_updated: str = "Not available"
    selected_candle_id: str = ""

    async def refresh(self) -> None:
        self.loading = True
        result = await TimeMachineApiClient().get_time_machine()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.error = None
            self.degraded = result.degraded
        else:
            self.data = {"available": False, "reason": TIME_MACHINE_MISSING}
            self.error = result.error
            self.degraded = True
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
