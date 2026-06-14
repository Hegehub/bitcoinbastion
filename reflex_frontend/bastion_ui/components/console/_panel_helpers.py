from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def preview_card(title: str, body: str) -> rx.Component:
    return card(rx.text(body), title=title)
