from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.market_empty_state import market_empty_state
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.signal_card import signal_card
from bastion_ui.components.market.signal_explanation_panel import signal_explanation_panel


def market_signals_page() -> rx.Component:
    return market_shell(
        "Market Signals",
        "Market observations with confidence, evidence links, and operator-review status.",
        responsive_grid(signal_card(), signal_explanation_panel()),
        market_empty_state("Signal records appear here when backend data is returned."),
    )
