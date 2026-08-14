from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt10_screens import sources_screen


def market_sources_page() -> rx.Component:
    return market_shell(
        "Market Sources",
        "Provider/source health, freshness, degraded state, and contribution visibility.",
        sources_screen(),
    )
