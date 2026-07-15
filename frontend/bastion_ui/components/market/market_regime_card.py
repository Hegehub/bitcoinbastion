from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_state import MarketState


def market_regime_card() -> rx.Component:
    return card(
        rx.text("Regime", weight="bold"),
        rx.text(MarketState.market_regime_label),
        rx.text("Confidence", weight="bold"),
        rx.text(MarketState.market_regime_confidence),
        rx.text("Evidence count", weight="bold"),
        rx.text(MarketState.market_regime_evidence_count),
        title="Current market regime",
        subtitle="Context only; not a trading recommendation.",
        badge=badge("Advisory", "info"),
        variant="console",
    )
