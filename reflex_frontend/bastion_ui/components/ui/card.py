from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import CARD, CONSOLE_PANEL, PANEL, SAFETY_CARD

CardVariant = Literal["default", "elevated", "safety", "console", "metric", "evidence"]


def card(
    *children: rx.Component,
    title: str | None = None,
    subtitle: str | None = None,
    badge: rx.Component | None = None,
    variant: CardVariant = "default",
) -> rx.Component:
    styles = {
        "default": CARD,
        "elevated": PANEL,
        "safety": SAFETY_CARD,
        "console": CONSOLE_PANEL,
        "metric": PANEL,
        "evidence": CARD,
    }
    header = []
    if title:
        header.append(rx.heading(title, size="4"))
    if subtitle:
        header.append(rx.text(subtitle, color="gray"))
    if badge:
        header.append(badge)
    return cast(
        rx.Component,
        rx.box(rx.vstack(*header, *children, align="start", spacing="3"), style=styles[variant]),
    )
