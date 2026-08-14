from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.footer import footer
from bastion_ui.components.layout.header import header
from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.public.safety_section import safety_section
from bastion_ui.theme.tokens import COLOR


def public_page(title: str, *children: rx.Component, subtitle: str | None = None) -> rx.Component:
    heading = rx.vstack(
        rx.heading(title, size="8"),
        rx.text(subtitle or "", color=COLOR["text_secondary"]),
        align="start",
        spacing="3",
        width="100%",
    )
    return public_layout(
        heading,
        *children,
        safety_section(),
        header=header(),
        footer=footer(),
    )


def link_card(label: str, href: str, description: str) -> rx.Component:
    from bastion_ui.components.ui.card import card

    return card(rx.text(description), rx.link(label, href=href), title=label)
