from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.public_client import get_status

STATUS_FALLBACK_MESSAGE = (
    "Status temporarily unavailable. This page cannot verify current backend health from the "
    "Reflex frontend."
)


class StatusState(rx.State):
    loading: bool = False
    error_message: str = ""
    stale: bool = True
    status: dict[str, Any] = {}

    async def load_status(self) -> None:
        self.loading = True
        try:
            data = await get_status()
            self.status = data if isinstance(data, dict) else {}
            self.error_message = ""
            self.stale = False
        except BastionApiError as exc:
            self.error_message = exc.public_message or STATUS_FALLBACK_MESSAGE
            self.stale = True
        finally:
            self.loading = False
