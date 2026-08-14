from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.topology import path_for


def evidence_packet_card() -> rx.Component:
    return card(
        rx.text("Evidence packets are audit material and supporting context."),
        rx.text("Replay status, source trail, quality, and confidence appear when available."),
        rx.link("Open Evidence overview", href=path_for("evidence")),
        title="Market evidence packet",
        variant="evidence",
    )
