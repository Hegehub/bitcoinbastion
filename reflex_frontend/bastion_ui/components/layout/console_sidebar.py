from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import CONSOLE_NAV_ITEMS, NavItem


def _console_status(item: NavItem) -> rx.Component:
    return cast(
        rx.Component,
        rx.badge(item.status.replace("_", " "), color_scheme="orange"),
    )


def console_sidebar() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Console", size="4"),
            *[
                rx.link(
                    rx.hstack(rx.text(item.label), _console_status(item), spacing="2"),
                    href=item.route,
                )
                for item in CONSOLE_NAV_ITEMS
            ],
            align="start",
            spacing="3",
            min_width="260px",
        ),
    )
