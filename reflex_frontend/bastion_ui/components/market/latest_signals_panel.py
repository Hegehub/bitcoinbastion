from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_state import MarketState


def latest_signals_panel() -> rx.Component:
    return card(
        rx.text(MarketState.latest_signals_label),
        rx.text(
            "Signals are advisory indicators and may be incomplete, stale, "
            "degraded, or wrong."
        ),
        rx.text("No trading instruction is provided."),
        title="Latest intelligence signals",
        subtitle="Backend signal availability is surfaced without creating recommendations.",
        badge=badge(MarketState.latest_signals_status, "warning"),
        variant="console",
    )
