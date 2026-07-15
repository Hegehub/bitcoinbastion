from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def time_machine_timeline() -> rx.Component:
    return card(
        rx.text("No Time Machine data available yet."),
        rx.text("Provider data may be stale, unavailable, or not configured."),
        rx.text("No trading or financial decision should be made from this empty state."),
        title="Historical timeline",
        badge=badge("empty", "warning"),
        variant="console",
    )
