from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def narrative_card() -> rx.Component:
    return card(
        rx.text(
            "This narrative is an evidence-based reconstruction, not a guaranteed "
            "explanation of price movement."
        ),
        rx.text("Contradictory evidence and uncertainty indicators are shown when available."),
        title="Narrative reconstruction",
        variant="console",
    )
