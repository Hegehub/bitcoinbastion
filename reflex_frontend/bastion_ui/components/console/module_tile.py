from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def module_tile(title: str, description: str, href: str = "#", planned: bool = False) -> rx.Component:
    suffix = " Planned." if planned else ""
    return card(rx.text(description + suffix), rx.link("Open" if not planned else "Planned", href=href), title=title)
