from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.market_intelligence_panel import market_intelligence_panel


def console_market_intelligence_page() -> rx.Component:
    return dashboard_shell(market_intelligence_panel())
