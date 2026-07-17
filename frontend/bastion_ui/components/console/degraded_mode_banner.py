from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

DEGRADED_MODE_COPY = (
    "Some Bastion data may be delayed, stale, degraded, or partially unavailable. "
    "Review provider health and evidence limitations before making decisions."
)


def degraded_mode_banner() -> rx.Component:
    return alert(DEGRADED_MODE_COPY, "degraded")
