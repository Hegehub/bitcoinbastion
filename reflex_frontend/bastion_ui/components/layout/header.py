from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import PUBLIC_NAV_ITEMS, NavItem
from bastion_ui.theme.styles import BUTTON_GHOST, BUTTON_SECONDARY, CONTAINER, FOCUS_RING
from bastion_ui.theme.tokens import (
    BASTION_BORDER,
    BASTION_PANEL,
    BASTION_TEXT,
    BASTION_TEXT_MUTED,
    BITCOIN_ORANGE,
)


def _status_label(item: NavItem) -> rx.Component:
    if item.status == "active":
        return cast(rx.Component, rx.fragment())
    return cast(
        rx.Component,
        rx.badge(item.status.replace("_", " ").title(), color_scheme="gray", size="1"),
    )


def nav_link(item: NavItem) -> rx.Component:
    return cast(
        rx.Component,
        rx.link(
            rx.hstack(rx.text(item.label), _status_label(item), spacing="1"),
            href=item.route,
            color=BASTION_TEXT,
            style=FOCUS_RING,
            aria_label=f"Open {item.label}",
        ),
    )


def public_header() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.box(
                            width="12px",
                            height="12px",
                            border_radius="999px",
                            background=BITCOIN_ORANGE,
                        ),
                        rx.text("Bitcoin Bastion", weight="bold", color=BASTION_TEXT),
                    ),
                    href="/",
                    aria_label="Bitcoin Bastion home",
                ),
                rx.hstack(
                    *[nav_link(item) for item in PUBLIC_NAV_ITEMS],
                    spacing="4",
                    display=["none", "none", "flex"],
                ),
                rx.spacer(),
                rx.link("Console", href="/console", style={**BUTTON_SECONDARY, **FOCUS_RING}),
                rx.button(
                    "⌘K", style={**BUTTON_GHOST, **FOCUS_RING}, aria_label="Open command palette"
                ),
                rx.button(
                    "Menu",
                    style={**BUTTON_GHOST, **FOCUS_RING},
                    display=["inline-flex", "inline-flex", "none"],
                    aria_label="Open mobile navigation",
                ),
                width="100%",
                max_width=CONTAINER["max_width"],
                padding=CONTAINER["padding"],
            ),
            background=BASTION_PANEL,
            border_bottom=f"1px solid {BASTION_BORDER}",
            color=BASTION_TEXT_MUTED,
            width="100%",
        ),
    )
