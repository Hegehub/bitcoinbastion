from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def signal_explanation_panel() -> rx.Component:
    return card(
        rx.text("Signal explanations are evidence-supported observations, not instructions."),
        rx.text("Suppression and operator review flags remain visible when exposed."),
        title="Signal explanation",
        variant="console",
    )
