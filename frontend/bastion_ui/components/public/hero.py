from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.theme.tokens import BASTION_TEXT_MUTED, BITCOIN_ORANGE


def public_hero(title: str, eyebrow: str, description: str) -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            badge(eyebrow, "info"),
            rx.heading(title, size="8", color=BITCOIN_ORANGE),
            rx.text(description, color=BASTION_TEXT_MUTED, size="4"),
            rx.hstack(
                rx.link(button("Open Trace", "primary"), href="/trace"),
                rx.link(button("Developer API", "secondary"), href="/developers"),
                rx.link(button("Operations", "ghost"), href="/operations"),
                spacing="3",
                wrap="wrap",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
