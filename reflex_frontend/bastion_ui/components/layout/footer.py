from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import FOOTER_NAV_ITEMS
from bastion_ui.theme.tokens import BASTION_BORDER, BASTION_TEXT_MUTED

FOOTER_SAFETY_COPY = (
    "Bitcoin Bastion is advisory-only software. It does not custody funds, request seed "
    "phrases, or provide legal verification."
)


def footer() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.hstack(
                    *[rx.link(item.label, href=item.route) for item in FOOTER_NAV_ITEMS],
                    spacing="4",
                    wrap="wrap",
                ),
                rx.text(FOOTER_SAFETY_COPY, color=BASTION_TEXT_MUTED),
                align="start",
                spacing="3",
            ),
            border_top=f"1px solid {BASTION_BORDER}",
            padding="24px",
        ),
    )
