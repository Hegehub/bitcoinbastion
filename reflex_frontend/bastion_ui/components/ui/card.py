from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CARD, CONSOLE_CARD, SAFETY_CARD


def card(*children: rx.Component, title: str | None = None) -> rx.Component:
    content = [rx.heading(title, size="4")] if title else []
    return cast(rx.Component, rx.box(*content, *children, style=CARD, width="100%"))


def safety_card(*children: rx.Component, title: str | None = None) -> rx.Component:
    content = [rx.heading(title, size="4")] if title else []
    return cast(rx.Component, rx.box(*content, *children, style=SAFETY_CARD, width="100%"))


def console_card(*children: rx.Component, title: str | None = None) -> rx.Component:
    content = [rx.heading(title, size="4")] if title else []
    return cast(rx.Component, rx.box(*content, *children, style=CONSOLE_CARD, width="100%"))
