from __future__ import annotations

import reflex as rx

from bastion_ui.components.market.market_intelligence_dashboard import market_intelligence_dashboard


def console_market_intelligence_page() -> rx.Component:
    return market_intelligence_dashboard()
