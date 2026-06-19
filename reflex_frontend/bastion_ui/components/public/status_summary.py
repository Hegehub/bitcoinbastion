from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.degraded_state import degraded_state
from bastion_ui.components.feedback.stale_data_banner import stale_data_banner
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card

STATUS_FALLBACK_COPY = (
    "Status temporarily unavailable. This page cannot verify current backend health from the "
    "Reflex frontend."
)


def status_summary(*, live_data_available: bool = False) -> rx.Component:
    if not live_data_available:
        return card(
            alert(STATUS_FALLBACK_COPY, "stale"),
            degraded_state("Backend status source unavailable for this Reflex preview."),
            stale_data_banner("Status data may be stale until the public status API is reachable."),
            title="Status fallback",
        )
    return card(rx.text("Backend status loaded from the public API."), title="Backend status")
