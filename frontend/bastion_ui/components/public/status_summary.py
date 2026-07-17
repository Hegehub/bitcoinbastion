from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card

STATUS_FALLBACK_COPY = (
    "Status temporarily unavailable. This page cannot verify current backend health from the "
    "Reflex frontend."
)


def status_fallback_card() -> rx.Component:
    return card(
        alert(STATUS_FALLBACK_COPY, "stale"),
        rx.text("Public status data should come from /api/v1/public/status when connected."),
        title="Backend health/status summary",
        subtitle="Safe fallback state",
    )
