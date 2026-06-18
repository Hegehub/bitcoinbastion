from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import FOOTER_NAV_ITEMS
from bastion_ui.theme.styles import CONTAINER, FOCUS_RING
from bastion_ui.theme.tokens import BASTION_BORDER, BASTION_TEXT_MUTED

FOOTER_SAFETY_COPY = (
    "Bitcoin Bastion is advisory-only software. It does not custody funds, request seed "
    "phrases, or provide legal verification."
)


def public_footer() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.hstack(
                    *[
                        rx.link(
                            item.label,
                            href=item.route,
                            style=FOCUS_RING,
                            aria_label=f"Open {item.label}",
                        )
                        for item in FOOTER_NAV_ITEMS
                    ],
                    spacing="4",
                    wrap="wrap",
                ),
                rx.text(FOOTER_SAFETY_COPY, color=BASTION_TEXT_MUTED),
                spacing="3",
                max_width=CONTAINER["max_width"],
                padding=CONTAINER["padding"],
                width="100%",
            ),
            border_top=f"1px solid {BASTION_BORDER}",
            width="100%",
        ),
    )
