from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_time_machine_state import MarketTimeMachineState


def time_machine_controls() -> rx.Component:
    return card(
        rx.text("Asset", weight="bold"),
        rx.text(MarketTimeMachineState.selected_asset),
        rx.text("Time range", weight="bold"),
        rx.hstack(
            badge("24h", "info"),
            badge("7d", "neutral"),
            badge("30d", "neutral"),
            wrap="wrap",
        ),
        title="Time range selector",
        subtitle="Explicit refresh actions are preferred over background polling.",
        variant="console",
    )
