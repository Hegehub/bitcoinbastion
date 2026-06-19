from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def error_state(message: str = "Unable to load this view safely.") -> rx.Component:
    return alert(message, "warning")
