from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_section_nav import market_section_nav
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.ui.card import card


def market_page() -> rx.Component:
    return market_shell(
        "Market Intelligence",
        "Reflex Market index for parity navigation. FastAPI/Jinja remains canonical until cutover.",
        card(
            rx.text(
                "Choose a Market section to review Time Machine, timeline, signals, "
                "evidence, narratives, or sources."
            ),
            market_section_nav(),
            title="Market sections",
            subtitle="Index page only; full public ownership is not cut over.",
            variant="console",
        ),
    )
