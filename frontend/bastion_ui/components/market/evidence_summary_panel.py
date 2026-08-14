from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.market_state import MarketState
from bastion_ui.topology import path_for


def evidence_summary_panel() -> rx.Component:
    return card(
        rx.text(MarketState.evidence_summary_label),
        rx.link("Open Evidence overview", href=path_for("evidence")),
        rx.text(
            "Missing evidence is shown as unavailable rather than filled with placeholder data."
        ),
        title="Evidence availability",
        subtitle="Evidence supports operator review and does not prove market outcomes.",
        badge=badge(MarketState.evidence_summary_status, "info"),
        variant="console",
    )
