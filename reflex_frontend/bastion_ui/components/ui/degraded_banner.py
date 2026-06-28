from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.security.safety_copy import DEGRADED_DATA


def degraded_banner(message: str = DEGRADED_DATA) -> rx.Component:
    return alert(message, "warning")
