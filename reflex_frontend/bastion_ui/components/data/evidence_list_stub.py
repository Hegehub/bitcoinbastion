from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def evidence_list_stub() -> rx.Component:
    return card(rx.text("Evidence list placeholder. Limited evidence shown."))
