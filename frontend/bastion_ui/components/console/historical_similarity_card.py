from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def historical_similarity_card() -> rx.Component:
    return card(
        rx.text("Historical similarity is not prediction."),
        rx.text("This view explains context and evidence, not future certainty."),
        title="Similarity lens",
        badge=badge("advisory", "info"),
        variant="console",
    )
