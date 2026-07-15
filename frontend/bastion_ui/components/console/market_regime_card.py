from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def market_regime_card() -> rx.Component:
    return card(
        rx.text("Market regime endpoint unavailable until backend DTO data is connected."),
        rx.text("Regime, confidence, and evidence counts are shown only when backend data exists."),
        title="Market regime",
        subtitle="Frontend shell complete, backend data source pending.",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
