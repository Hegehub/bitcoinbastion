from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.theme.styles import SECTION


def public_hero(
    title: str,
    subtitle: str,
    *,
    eyebrow: str = "Bitcoin Bastion",
    primary_label: str | None = None,
    primary_href: str = "/trace",
    secondary_label: str | None = None,
    secondary_href: str = "/developers",
) -> rx.Component:
    actions: list[rx.Component] = []
    if primary_label:
        actions.append(rx.link(button(primary_label), href=primary_href))
    if secondary_label:
        actions.append(rx.link(button(secondary_label, "secondary"), href=secondary_href))
    return cast(
        rx.Component,
        rx.section(
            rx.vstack(
                badge(eyebrow, "info"),
                rx.heading(title, size="9", as_="h1"),
                rx.text(subtitle, size="4", max_width="860px"),
                rx.hstack(*actions, spacing="3", wrap="wrap") if actions else rx.fragment(),
                align="start",
                spacing="5",
            ),
            style=SECTION,
        ),
    )
