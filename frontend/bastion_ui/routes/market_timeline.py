from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt10_screens import replay_screen, timeline_screen


def market_timeline_page() -> rx.Component:
    return market_shell(
        "Market Timeline",
        "Timeline of market-relevant events with source attribution and evidence links.",
        timeline_screen(),
        replay_screen(),
    )
