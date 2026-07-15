from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.market_empty_state import market_empty_state
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.source_health_card import source_health_card


def market_sources_page() -> rx.Component:
    return market_shell(
        "Market Sources",
        "Provider/source health, freshness, degraded state, and contribution visibility.",
        responsive_grid(source_health_card()),
        market_empty_state("Sources appear here when backend source data is returned."),
    )
