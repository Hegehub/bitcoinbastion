from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.time_machine_panel import time_machine_panel
from bastion_ui.components.wow.historical_similarity_lens import historical_similarity_lens
from bastion_ui.components.wow.market_intelligence_wall import market_intelligence_wall


def console_time_machine_page() -> rx.Component:
    return dashboard_shell(
        time_machine_panel(), historical_similarity_lens(), market_intelligence_wall()
    )
