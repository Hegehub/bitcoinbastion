from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def limitations_card(*limitations: str) -> rx.Component:
    items = limitations or ("This view may be incomplete.", "Manual review recommended.")
    return card(
        rx.unordered_list(*[rx.list_item(item) for item in items]),
        title="Limitations",
        variant="safety",
    )
