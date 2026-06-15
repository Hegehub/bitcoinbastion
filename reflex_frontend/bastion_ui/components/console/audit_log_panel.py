from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def audit_log_panel() -> rx.Component:
    return card(rx.text("Audit log placeholder. No execution controls are exposed in this Reflex prompt."), title="Audit Log")
