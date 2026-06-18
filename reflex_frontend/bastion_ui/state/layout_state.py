from __future__ import annotations

import reflex as rx


class LayoutState(rx.State):
    sidebar_open: bool = True

    def set_sidebar_open(self, value: bool) -> None:
        self.sidebar_open = value

    def toggle_sidebar(self) -> None:
        self.sidebar_open = not self.sidebar_open
