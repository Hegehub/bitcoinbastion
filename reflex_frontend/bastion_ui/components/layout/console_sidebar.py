from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import CONSOLE_NAV_ITEMS, NavItem
from bastion_ui.theme.styles import FOCUS_RING, PANEL


def _console_status(item: NavItem) -> rx.Component:
    if item.status == "active":
        return cast(rx.Component, rx.fragment())
    return cast(
        rx.Component,
        rx.badge(item.status.replace("_", " ").title(), color_scheme="gray", size="1"),
    )


def console_sidebar() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Console", weight="bold"),
            *[
                rx.link(
                    rx.hstack(rx.text(item.label), _console_status(item), spacing="2"),
                    href=item.route,
                    style=FOCUS_RING,
                    aria_label=f"Open {item.label}",
                )
                for item in CONSOLE_NAV_ITEMS
            ],
            rx.text("Preview routes do not imply live backend parity.", size="2"),
            style=PANEL,
            spacing="3",
            width="280px",
        ),
    )
