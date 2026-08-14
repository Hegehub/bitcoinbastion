from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt9_screens import market_signals_screen


def market_signals_page() -> rx.Component:
    return market_shell(
        "Market Signals",
        "Backend analytical signals; not trade instructions or automatic execution.",
        market_signals_screen(),
    )
