from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.audit_client import AuditApiClient

AUDIT_ENDPOINT_MISSING = "Audit events endpoint is not available yet."


class ConsoleAuditState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    last_updated: str = "Not available"
    degraded: bool = True

    async def refresh(self) -> None:
        self.loading = True
        result = await AuditApiClient().get_audit_events()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.error = None
            self.degraded = result.degraded
        else:
            self.data = {
                "available": False,
                "reason": AUDIT_ENDPOINT_MISSING,
                "future_endpoint": "/api/v1/audit/events",
            }
            self.error = result.error
            self.degraded = True
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
