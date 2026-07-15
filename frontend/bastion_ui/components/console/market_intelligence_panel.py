from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.market_regime_card import market_regime_card
from bastion_ui.components.console.provider_freshness_card import provider_freshness_card
from bastion_ui.components.console.signal_summary_card import signal_summary_card
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

MARKET_INTELLIGENCE_SAFETY_COPY = (
    "Market intelligence is advisory-only. This is not financial advice. "
    "Signals may be stale, incomplete, or provider-dependent. "
    "Always review evidence and limitations before acting."
)


def market_intelligence_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Market Intelligence", size="6"),
            rx.text(
                "Operator-facing market intelligence summary with evidence and freshness context."
            ),
            card(rx.text(MARKET_INTELLIGENCE_SAFETY_COPY), title="Market safety", variant="safety"),
            degraded_state_banner(),
            responsive_grid(market_regime_card(), signal_summary_card(), provider_freshness_card()),
            card(
                rx.text(
                    "Latest intelligence signals endpoint is unavailable or not connected yet."
                ),
                rx.text("Signals are displayed only when backend data is returned."),
                title="Latest signals",
                badge=badge("unavailable", "warning"),
                variant="console",
            ),
            card(
                rx.text("Evidence-linked market events are pending backend DTO support."),
                rx.link("Open Market Evidence", href="/market/evidence"),
                title="Evidence-linked events",
                variant="console",
            ),
            card(
                rx.text(
                    "Operator warnings: provider freshness, stale data, and "
                    "low confidence reduce utility."
                ),
                rx.text("No market output should be treated as trading instruction."),
                title="Operator warnings and limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
