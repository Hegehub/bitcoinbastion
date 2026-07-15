from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.errors import BastionFrontendError
from bastion_ui.services.status_client import StatusApiClient

CONSOLE_UNKNOWN = "unknown"
CONSOLE_DEGRADED_MESSAGE = (
    "Some Bastion data may be delayed, stale, degraded, or partially unavailable."
)


class ConsoleState(rx.State):
    api_status: str = CONSOLE_UNKNOWN
    trace_status: str = CONSOLE_UNKNOWN
    evidence_status: str = CONSOLE_UNKNOWN
    provider_status: str = CONSOLE_UNKNOWN
    market_status: str = CONSOLE_UNKNOWN
    policy_status: str = CONSOLE_UNKNOWN
    audit_status: str = CONSOLE_UNKNOWN
    runtime_status: str = CONSOLE_UNKNOWN
    environment_label: str = CONSOLE_UNKNOWN
    last_updated: str = "Not available"
    degraded_reasons: list[str] = [CONSOLE_DEGRADED_MESSAGE]
    status_payload: dict[str, Any] = {}

    async def load_status(self) -> None:
        try:
            payload = await StatusApiClient().get_public_status()
        except BastionFrontendError as exc:
            self.api_status = "degraded"
            self.degraded_reasons = [getattr(exc, "public_message", CONSOLE_DEGRADED_MESSAGE)]
            return
        except Exception:  # pragma: no cover - defensive console fallback
            self.api_status = "unavailable"
            self.degraded_reasons = [CONSOLE_DEGRADED_MESSAGE]
            return

        self.status_payload = payload if isinstance(payload, dict) else {}
        self.api_status = str(self.status_payload.get("status") or CONSOLE_UNKNOWN)
        self.runtime_status = str(self.status_payload.get("runtime") or CONSOLE_UNKNOWN)
        self.environment_label = str(self.status_payload.get("environment") or CONSOLE_UNKNOWN)
        self.last_updated = str(
            self.status_payload.get("updated_at")
            or self.status_payload.get("last_updated")
            or "Not available"
        )
        degraded = bool(self.status_payload.get("degraded") or self.status_payload.get("stale"))
        self.degraded_reasons = [CONSOLE_DEGRADED_MESSAGE] if degraded else []

    def clear_status(self) -> None:
        self.api_status = CONSOLE_UNKNOWN
        self.trace_status = CONSOLE_UNKNOWN
        self.evidence_status = CONSOLE_UNKNOWN
        self.provider_status = CONSOLE_UNKNOWN
        self.market_status = CONSOLE_UNKNOWN
        self.policy_status = CONSOLE_UNKNOWN
        self.audit_status = CONSOLE_UNKNOWN
        self.runtime_status = CONSOLE_UNKNOWN
        self.environment_label = CONSOLE_UNKNOWN
        self.last_updated = "Not available"
        self.degraded_reasons = [CONSOLE_DEGRADED_MESSAGE]
        self.status_payload = {}
