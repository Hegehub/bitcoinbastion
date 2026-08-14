from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt10_screens import attribution_screen, replay_screen


def market_time_machine_page() -> rx.Component:
    return market_shell(
        "Bastion Market Time Machine",
        "Evidence-driven BTC market reconstruction for operator review.",
        replay_screen(),
        attribution_screen(),
    )
