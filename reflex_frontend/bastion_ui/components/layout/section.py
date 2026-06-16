from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import SECTION


def section(*children: rx.Component, title: str | None = None) -> rx.Component:
    content = []
    if title:
        content.append(rx.heading(title, size="5"))
    content.extend(children)
    return cast(
        rx.Component,
        rx.box(rx.vstack(*content, align="start", spacing="4"), style=SECTION),
    )
