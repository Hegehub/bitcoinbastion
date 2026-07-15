from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.market_intelligence_panel import market_intelligence_panel
from bastion_ui.components.wow.historical_similarity_lens import historical_similarity_lens
from bastion_ui.components.wow.market_intelligence_wall import market_intelligence_wall
from bastion_ui.components.wow.risk_heatmap import risk_heatmap


def console_market_intelligence_page() -> rx.Component:
    return dashboard_shell(
        market_intelligence_panel(),
        market_intelligence_wall(),
        risk_heatmap(),
        historical_similarity_lens(),
    )
