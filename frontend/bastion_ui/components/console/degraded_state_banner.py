from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

CONSOLE_MODULE_DEGRADED_COPY = (
    "Module data may be incomplete, stale, degraded, unavailable, or limited by backend endpoints. "
    "Use this console as operator review context only."
)


def degraded_state_banner() -> rx.Component:
    return alert(CONSOLE_MODULE_DEGRADED_COPY, "degraded")
