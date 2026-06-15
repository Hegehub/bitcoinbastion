from __future__ import annotations

from typing import Any

import reflex as rx


class ConsoleState(rx.State):
    degraded_message: str = "Console data may be delayed, degraded, stale, or unavailable."
    selected_module: str = "Dashboard"
    loading: bool = False
    error: str = ""
    degraded: bool = True
    last_updated: str | None = None
    data: dict[str, Any] = {}

    def select_module(self, module: str) -> None:
        self.selected_module = module

    async def load(self) -> None:
        self.loading = False
        self.degraded = True
        self.data = {"message": "Read-only fallback preview."}

    async def refresh(self) -> None:
        await self.load()

    def clear_error(self) -> None:
        self.error = ""
