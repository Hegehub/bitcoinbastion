from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.state.market_state import MarketState


def market_status_banner() -> rx.Component:
    return cast(
        rx.Component,
        rx.cond(
            MarketState.degraded_reasons,
            alert(
                "Market data is degraded or partially unavailable. Review provider status "
                "and verify independently before acting.",
                "degraded",
            ),
            alert(
                "Market dashboard is display-only and may show stale or unavailable data.",
                "advisory",
            ),
        ),
    )
