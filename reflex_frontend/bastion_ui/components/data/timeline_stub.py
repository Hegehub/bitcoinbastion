from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def timeline_stub() -> rx.Component:
    return card(rx.text("Timeline placeholder. No backend data connected."))
