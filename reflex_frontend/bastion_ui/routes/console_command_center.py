from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.wow.animated_core import animated_core
from bastion_ui.components.wow.bastion_command_center import bastion_command_center
from bastion_ui.components.wow.no_custody_safety_layer import no_custody_safety_layer
from bastion_ui.components.wow.node_pulse import node_pulse
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix
from bastion_ui.components.wow.risk_heatmap import risk_heatmap
from bastion_ui.components.wow.sovereignty_score_panel import sovereignty_score_panel


def console_command_center_page() -> rx.Component:
    return dashboard_shell(
        "Bastion Command Center",
        rx.vstack(
            console_page_header("Bastion Command Center", "Preview only. Backend remains the source of truth."),
            console_status_strip(),
            no_custody_safety_layer(),
            bastion_command_center(),
            sovereignty_score_panel(),
            provider_trust_matrix(),
            node_pulse(),
            risk_heatmap(),
            animated_core(),
            spacing="4",
            width="100%",
        ),
    )
