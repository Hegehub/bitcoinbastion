from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def market_error_state(message: str = "Market data is temporarily unavailable.") -> rx.Component:
    return alert(message, "degraded")
