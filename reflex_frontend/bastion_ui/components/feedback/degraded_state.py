from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def degraded_state() -> rx.Component:
    return alert(
        "Data source degraded. Some providers are unavailable. Manual review recommended.",
        "degraded",
    )
