from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt9_screens import market_overview_screen


def market_page() -> rx.Component:
    return market_shell(
        "Market Overview",
        "Current backend-authoritative Bitcoin market measurements and source posture.",
        market_overview_screen(),
    )
