from __future__ import annotations

import reflex as rx


class NavigationState(rx.State):
    mobile_nav_open: bool = False

    def set_mobile_nav_open(self, value: bool) -> None:
        self.mobile_nav_open = value

    def toggle_mobile_nav(self) -> None:
        self.mobile_nav_open = not self.mobile_nav_open
