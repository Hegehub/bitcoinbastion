from __future__ import annotations

import reflex as rx


class CommandPaletteState(rx.State):
    open: bool = False
    query: str = ""

    def set_open(self, value: bool) -> None:
        self.open = value

    def toggle_open(self) -> None:
        self.open = not self.open

    def set_query(self, value: str) -> None:
        self.query = value
