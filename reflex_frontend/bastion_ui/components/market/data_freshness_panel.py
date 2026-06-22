from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_state import MarketState


def data_freshness_panel() -> rx.Component:
    return card(
        rx.text("Last updated", weight="bold"),
        rx.text(MarketState.last_updated_at),
        rx.text(MarketState.freshness_label),
        title="Data freshness",
        subtitle="Stale and unavailable states remain visible.",
        badge=badge(MarketState.freshness_status, "warning"),
        variant="console",
    )
