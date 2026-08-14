from __future__ import annotations

import reflex as rx
from reflex.event import EventSpec


class NavigationState(rx.State):
    mobile_nav_open: bool = False

    @rx.var
    def current_path(self) -> str:
        return self.router.url.path

    def set_mobile_nav_open(self, value: bool) -> EventSpec | None:
        self.mobile_nav_open = value
        if not value:
            return rx.set_focus("mobile-navigation-trigger")
        return None

    def toggle_mobile_nav(self) -> EventSpec | None:
        self.mobile_nav_open = not self.mobile_nav_open
        if not self.mobile_nav_open:
            return rx.set_focus("mobile-navigation-trigger")
        return rx.set_focus("mobile-navigation-close")
