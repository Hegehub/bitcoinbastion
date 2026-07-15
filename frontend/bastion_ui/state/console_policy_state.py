from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.services.policy_client import PolicyApiClient

POLICY_ENDPOINT_MISSING = "Global policy listing endpoint is not available yet."


class ConsolePolicyState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    last_updated: str = "Not available"
    degraded: bool = True
    report_id: str = ""

    async def refresh(self) -> None:
        self.loading = True
        result = await PolicyApiClient().get_policy_baseline()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.error = None
            self.degraded = result.degraded
        else:
            self.data = {
                "available": False,
                "reason": POLICY_ENDPOINT_MISSING,
                "future_endpoint": "/api/v1/policy",
            }
            self.error = result.error
            self.degraded = True
        self.loading = False

    async def submit_report_lookup(self) -> None:
        validation = validate_report_id(self.report_id)
        if not validation.ok:
            self.error = validation.error
            return
        self.loading = True
        result = await PolicyApiClient().get_policy_facts(validation.report_id)
        self.data = result.data if isinstance(result.data, dict) else {}
        self.error = result.error
        self.degraded = result.degraded or not result.ok
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
