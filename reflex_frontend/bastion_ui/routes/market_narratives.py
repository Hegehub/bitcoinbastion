from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.market_empty_state import market_empty_state
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.narrative_card import narrative_card
from bastion_ui.components.market.source_health_card import source_health_card


def market_narratives_page() -> rx.Component:
    return market_shell(
        "Market Narratives",
        "Evidence-based reconstruction of market context with visible uncertainty.",
        responsive_grid(narrative_card(), source_health_card()),
        market_empty_state("Narratives appear here when backend data is returned."),
    )
