from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt10_screens import narratives_screen


def market_narratives_page() -> rx.Component:
    return market_shell(
        "Market Narratives",
        "Evidence-based reconstruction of market context with visible uncertainty.",
        narratives_screen(),
    )
