from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.security.market_safety_copy import MARKET_TIME_MACHINE_SAFETY_COPY


def market_safety_banner() -> rx.Component:
    return alert(MARKET_TIME_MACHINE_SAFETY_COPY, "advisory")
