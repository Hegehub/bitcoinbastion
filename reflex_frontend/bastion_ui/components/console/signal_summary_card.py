from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def signal_summary_card() -> rx.Component:
    return card(
        rx.text("Signals may be stale, incomplete, or provider-dependent."),
        rx.text("No market signal is shown as a trading instruction."),
        title="Signal confidence overview",
        badge=badge("advisory", "info"),
        variant="console",
    )
