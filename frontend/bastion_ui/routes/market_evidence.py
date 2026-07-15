from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.evidence_packet_card import evidence_packet_card
from bastion_ui.components.market.market_empty_state import market_empty_state
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.source_health_card import source_health_card


def market_evidence_page() -> rx.Component:
    return market_shell(
        "Market Evidence",
        "Evidence packets as audit material, supporting context, and source trails.",
        responsive_grid(evidence_packet_card(), source_health_card()),
        market_empty_state("Evidence packets appear here when backend data is returned."),
    )
