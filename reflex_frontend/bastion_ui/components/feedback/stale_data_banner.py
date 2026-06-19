from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def stale_data_banner(message: str = "Stale data. Manual review recommended.") -> rx.Component:
    return alert(message, "stale")
