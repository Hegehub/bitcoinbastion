from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_policy_facts_panel() -> rx.Component:
    return card(
        rx.text("Policy facts, warnings, and manual-review requirements appear when available."),
        rx.text("This panel does not provide legal or payment approval."),
        title="Policy facts",
    )
