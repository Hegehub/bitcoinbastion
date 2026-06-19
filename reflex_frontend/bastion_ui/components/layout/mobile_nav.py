from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import MOBILE_NAV_ITEMS
from bastion_ui.theme.styles import CARD, FOCUS_RING

MOBILE_NAV_SAFETY_COPY = "No custody. Public Bitcoin addresses only. Never enter signing material."


def mobile_nav() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Navigation", weight="bold"),
            *[
                rx.link(
                    item.label,
                    href=item.route,
                    width="100%",
                    style=FOCUS_RING,
                    aria_label=f"Open {item.label}",
                )
                for item in MOBILE_NAV_ITEMS
            ],
            rx.text(MOBILE_NAV_SAFETY_COPY, size="2"),
            style=CARD,
            spacing="3",
            width="100%",
        ),
    )
