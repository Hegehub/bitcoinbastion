from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def candle_attribution_card() -> rx.Component:
    return card(
        rx.text("Candle reference: Not available"),
        rx.text("Attributed events and confidence appear only when backend data is returned."),
        rx.text("Evidence links remain visible when supplied by the DTO."),
        title="Candle attribution",
        variant="console",
    )
