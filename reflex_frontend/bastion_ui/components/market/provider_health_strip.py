from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_state import MarketState


def provider_health_strip() -> rx.Component:
    return card(
        rx.text(MarketState.provider_health_label),
        rx.text("Provider health must remain visible so degraded or stale data is not hidden."),
        title="Provider health overview",
        subtitle=(
            "Healthy, degraded, stale, offline, or unavailable states are shown "
            "when exposed."
        ),
        badge=badge(MarketState.provider_health_status, "warning"),
        variant="console",
    )
