from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def forbidden_input_notice() -> rx.Component:
    return alert(
        "Do not enter wallet secrets or signing material. Use public Bitcoin addresses only.",
        "danger",
    )
