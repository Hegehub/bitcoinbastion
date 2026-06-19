from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CARD


def empty_state(title: str, description: str, action: rx.Component | None = None) -> rx.Component:
    content = [rx.heading(title, size="4"), rx.text(description, color="gray")]
    if action is not None:
        content.append(action)
    return cast(rx.Component, rx.box(rx.vstack(*content, align="start"), style=CARD))
