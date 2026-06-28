from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.command_palette import command_palette_trigger
from bastion_ui.components.layout.mobile_nav import mobile_nav_trigger
from bastion_ui.navigation import PUBLIC_NAV_ITEMS, NavItem
from bastion_ui.theme.styles import FOCUS_RING
from bastion_ui.theme.tokens import BASTION_BORDER, BITCOIN_ORANGE


def _status_label(item: NavItem) -> rx.Component:
    if item.status == "active":
        return cast(rx.Component, rx.fragment())
    return cast(
        rx.Component,
        rx.badge(item.status.replace("_", " "), color_scheme="orange"),
    )


def header() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.hstack(
                rx.link(
                    "Bitcoin Bastion",
                    href="/",
                    color=BITCOIN_ORANGE,
                    weight="bold",
                    style=FOCUS_RING,
                ),
                rx.hstack(
                    *[
                        rx.link(
                            rx.hstack(rx.text(item.label), _status_label(item), spacing="1"),
                            href=item.route,
                            style=FOCUS_RING,
                        )
                        for item in PUBLIC_NAV_ITEMS
                    ],
                    spacing="3",
                    wrap="wrap",
                ),
                rx.spacer(),
                rx.link("Console", href="/console", style=FOCUS_RING),
                command_palette_trigger(),
                mobile_nav_trigger(),
                width="100%",
                align="center",
            ),
            border_bottom=f"1px solid {BASTION_BORDER}",
            padding="16px 24px",
        ),
    )
