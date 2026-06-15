from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.safety_banner import advisory_banner, no_custody_banner


def page_shell(title: str, subtitle: str, cards: tuple[tuple[str, str], ...]) -> rx.Component:
    return public_layout(cast(rx.Component, rx.vstack(
        rx.heading(title, size="8"),
        rx.text(subtitle, size="4"),
        no_custody_banner(),
        advisory_banner(),
        rx.grid(*[card(rx.text(body), title=heading) for heading, body in cards], columns="2", spacing="4", width="100%"),
        spacing="5",
        align="start",
        width="100%",
    )))
