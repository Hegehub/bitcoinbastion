from __future__ import annotations

from typing import Any

import reflex as rx


class ConsoleDataState(rx.State):
    loading: bool = False
    error: str = ""
    degraded: bool = True
    last_updated: str | None = None
    data: dict[str, Any] = {}

    async def load(self) -> None:
        self.loading = True
        self.error = ""
        self.degraded = True
        self.data = {"message": "Backend data unavailable; fallback preview is visible."}
        self.last_updated = None
        self.loading = False

    async def refresh(self) -> None:
        await self.load()

    def clear_error(self) -> None:
        self.error = ""
