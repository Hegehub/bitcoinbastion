from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.market.candle_attribution_card import candle_attribution_card
from bastion_ui.components.market.evidence_packet_card import evidence_packet_card
from bastion_ui.components.market.market_regime_card import market_regime_card
from bastion_ui.components.market.market_shell import market_shell
from bastion_ui.components.market.narrative_card import narrative_card
from bastion_ui.components.market.signal_card import signal_card
from bastion_ui.components.market.source_health_card import source_health_card
from bastion_ui.components.market.time_machine_controls import time_machine_controls
from bastion_ui.components.market.time_machine_header import time_machine_header
from bastion_ui.components.market.time_machine_timeline import time_machine_timeline


def market_time_machine_page() -> rx.Component:
    return market_shell(
        "Bastion Market Time Machine",
        "Evidence-driven BTC market reconstruction for operator review.",
        time_machine_header(),
        time_machine_controls(),
        responsive_grid(
            market_regime_card(),
            time_machine_timeline(),
            candle_attribution_card(),
            signal_card(),
            evidence_packet_card(),
            narrative_card(),
            source_health_card(),
        ),
    )
