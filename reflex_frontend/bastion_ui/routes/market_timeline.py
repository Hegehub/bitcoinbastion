from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.market_empty_state import market_empty_state
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.source_health_card import source_health_card
from bastion_ui.components.market.time_machine_timeline import time_machine_timeline


def market_timeline_page() -> rx.Component:
    return market_shell(
        "Market Timeline",
        "Timeline of market-relevant events with source attribution and evidence links.",
        responsive_grid(time_machine_timeline(), source_health_card()),
        market_empty_state("Events appear here when backend timeline data is returned."),
    )
