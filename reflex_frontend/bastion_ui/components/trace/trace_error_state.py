from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def trace_error_state(message: str) -> rx.Component:
    return alert(message, "warning")
