from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card
from bastion_ui.components.wow.api_contract_explorer import api_contract_explorer
from bastion_ui.components.wow.audit_replay_timeline import audit_replay_timeline
from bastion_ui.components.wow.citadel_mode_panel import citadel_mode_panel
from bastion_ui.components.wow.degraded_mode_banner import wow_degraded_mode_banner
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
from bastion_ui.components.wow.market_intelligence_wall import market_intelligence_wall
from bastion_ui.components.wow.node_pulse import node_pulse
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix
from bastion_ui.components.wow.risk_heatmap import risk_heatmap
from bastion_ui.components.wow.sovereignty_score_panel import sovereignty_score_panel
from bastion_ui.components.wow.trace_radar import trace_radar

WOW_SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files "
    "or signing material."
)


def console_wow_page() -> rx.Component:
    return dashboard_shell(
        rx.vstack(
            rx.heading("Bastion Wow Layer", size="7"),
            rx.text(
                "Operator-oriented visual layer for Trace, Evidence, Provider Health, "
                "Market Intelligence, Policy, Audit, and runtime posture."
            ),
            card(rx.text(WOW_SAFETY_COPY), title="Visual safety", variant="safety"),
            card(
                rx.text("Live operational data is unavailable."),
                rx.text("This panel is displaying safe unavailable states only."),
                title="Unavailable data summary",
                variant="console",
            ),
            wow_degraded_mode_banner(),
            responsive_grid(
                trace_radar(),
                evidence_chain_viewer(),
                provider_trust_matrix(),
                node_pulse(),
                sovereignty_score_panel(),
                risk_heatmap(),
                market_intelligence_wall(),
                audit_replay_timeline(),
                api_contract_explorer(),
                citadel_mode_panel(),
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )
