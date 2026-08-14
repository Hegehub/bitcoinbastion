from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.console_layout import console_layout
from bastion_ui.components.layout.console_sidebar import console_sidebar
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.data_freshness_panel import data_freshness_panel
from bastion_ui.components.market.evidence_summary_panel import evidence_summary_panel
from bastion_ui.components.market.latest_signals_panel import latest_signals_panel
from bastion_ui.components.market.market_regime_card import market_regime_card
from bastion_ui.components.market.market_status_banner import market_status_banner
from bastion_ui.components.market.provider_health_strip import provider_health_strip
from bastion_ui.components.market.time_machine_teaser import time_machine_teaser
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.button import button
from bastion_ui.security.market_safety import MARKET_NO_CUSTODY_COPY, MARKET_SAFETY_COPY
from bastion_ui.topology import path_for


def market_intelligence_dashboard() -> rx.Component:
    return console_layout(
        rx.vstack(
            rx.heading("Market Intelligence", size="7"),
            rx.text(
                "Operator overview of market intelligence, signal state, provider health, "
                "evidence availability, and degraded data conditions."
            ),
            alert(MARKET_SAFETY_COPY, "advisory"),
            alert(MARKET_NO_CUSTODY_COPY, "info"),
            market_status_banner(),
            button("Refresh market overview", "secondary"),
            responsive_grid(
                market_regime_card(),
                latest_signals_panel(),
                provider_health_strip(),
                evidence_summary_panel(),
                data_freshness_panel(),
                time_machine_teaser(),
            ),
            rx.link("Open developer API docs", href=path_for("developers")),
            align="start",
            spacing="5",
            width="100%",
        ),
        sidebar=console_sidebar(),
    )
