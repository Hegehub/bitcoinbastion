from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.public.roadmap_preview import CONSERVATIVE_ROADMAP_STATUSES
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.public_client import get_roadmap


class RoadmapState(rx.State):
    loading: bool = False
    error_message: str = ""
    stale: bool = True
    roadmap: list[dict[str, Any]] = []

    async def load_roadmap(self) -> None:
        self.loading = True
        try:
            data = await get_roadmap()
            self.roadmap = data if isinstance(data, list) else []
            self.error_message = ""
            self.stale = False
        except BastionApiError as exc:
            self.error_message = exc.public_message
            self.stale = True
        finally:
            self.loading = False

    @rx.var
    def conservative_labels(self) -> list[str]:
        return list(CONSERVATIVE_ROADMAP_STATUSES)
