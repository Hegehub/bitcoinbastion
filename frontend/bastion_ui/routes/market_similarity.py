from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.prompt10_screens import replay_screen
from bastion_ui.components.prompt11_screens import similarity_screen


def market_similarity_page() -> rx.Component:
    return market_shell(
        "Historical Similarity",
        "Backend-ranked historical context comparison. This surface is not a forecast.",
        similarity_screen(),
        replay_screen(),
    )
