from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def forbidden_input_notice() -> rx.Component:
    return alert(
        "Never enter seed phrases, private keys, wallet files or signing material.",
        "warning",
    )
