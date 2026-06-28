from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.market.market_limitations_card import market_limitations_card
from bastion_ui.components.market.market_safety_banner import market_safety_banner
from bastion_ui.components.market.market_section_nav import market_section_nav
from bastion_ui.components.ui.alert import alert


def market_shell(
    title: str,
    description: str,
    *children: rx.Component,
    degraded: bool = True,
) -> rx.Component:
    return public_layout(
        rx.vstack(
            rx.heading(title, size="7"),
            rx.text(description),
            market_section_nav(),
            market_safety_banner(),
            rx.cond(
                degraded,
                alert(
                    "Market data may be degraded, stale, incomplete, or unavailable. "
                    "Provider disagreement must remain visible.",
                    "degraded",
                ),
                rx.fragment(),
            ),
            *children,
            market_limitations_card(),
            align="start",
            spacing="5",
            width="100%",
        )
    )
