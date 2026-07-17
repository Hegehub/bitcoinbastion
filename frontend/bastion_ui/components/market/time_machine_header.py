from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def time_machine_header() -> rx.Component:
    return card(
        rx.text("BTC-focused evidence-driven market reconstruction."),
        rx.text("Historical similarity is advisory-only and does not guarantee repetition."),
        title="Bastion Market Time Machine",
        badge=badge("BTC", "info"),
        variant="console",
    )
