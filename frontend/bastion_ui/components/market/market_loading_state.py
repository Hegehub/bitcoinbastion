from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.loading_state import loading_state


def market_loading_state() -> rx.Component:
    return loading_state("Loading market data")
