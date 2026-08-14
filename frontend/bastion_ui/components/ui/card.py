from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.materials import material_style
from bastion_ui.theme.styles import CARD, CONSOLE_PANEL, PANEL, SAFETY_CARD
from bastion_ui.theme.tokens import COLOR, MaterialLevel

CardVariant = Literal[
    "default", "matte", "glass", "elevated", "safety", "console", "metric", "evidence"
]


def card(
    *children: rx.Component,
    title: str | None = None,
    subtitle: str | None = None,
    badge: rx.Component | None = None,
    variant: CardVariant = "default",
) -> rx.Component:
    styles = {
        "default": CARD,
        "matte": material_style(MaterialLevel.MATTE),
        "glass": material_style(MaterialLevel.GLASS_SUBTLE),
        "elevated": PANEL,
        "safety": SAFETY_CARD,
        "console": CONSOLE_PANEL,
        "metric": PANEL,
        "evidence": CARD,
    }
    header = []
    if title or badge:
        header.append(
            rx.hstack(
                rx.heading(title or "", size="4", as_="h2"),
                badge or rx.fragment(),
                justify="between",
                width="100%",
            )
        )
    if subtitle:
        header.append(rx.text(subtitle, color=COLOR["text_secondary"]))
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(*header, *children, align="start", spacing="3"),
            width="100%",
            style=styles[variant],
            class_name="bb-glass" if variant in {"glass", "elevated", "metric"} else None,
        ),
    )
