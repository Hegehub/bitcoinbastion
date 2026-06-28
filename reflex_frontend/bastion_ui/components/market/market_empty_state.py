from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.empty_state import empty_state


def market_empty_state(
    message: str = "No market data returned by the backend yet.",
) -> rx.Component:
    return empty_state("Market data unavailable", message)
