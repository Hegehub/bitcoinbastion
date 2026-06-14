from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import safety_card


def trace_limitations_card() -> rx.Component:
    return safety_card(rx.text("Trace is advisory-only, not legal verification, and not Bitcoin consensus proof. Results may be incomplete when providers disagree or data is unavailable."), title="Limitations")
