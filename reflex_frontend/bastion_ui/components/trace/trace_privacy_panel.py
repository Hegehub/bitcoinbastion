from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_privacy_panel() -> rx.Component:
    return card(
        rx.text("Privacy exposure, reuse indicators, and clustering risk appear when available."),
        rx.text("Manual review recommended for operational privacy context."),
        title="Privacy exposure",
    )
