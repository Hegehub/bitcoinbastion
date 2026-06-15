from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.bastion_command_center import bastion_command_center
from bastion_ui.components.wow.sovereignty_score_panel import sovereignty_score_panel
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix
from bastion_ui.components.wow.risk_heatmap import risk_heatmap
from bastion_ui.components.wow.no_custody_safety_layer import no_custody_safety_layer
from bastion_ui.components.console.audit_log_panel import audit_log_panel
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.ui.safety_banner import safety_banner


def console_page() -> rx.Component:
    return dashboard_shell("Bastion Console", rx.vstack(
        rx.text("Operator-facing command center. Display-only in this prompt; no execution controls, custody controls, or signing controls are exposed."),
        safety_banner("console"),
            bastion_command_center(),
            sovereignty_score_panel(),
            provider_trust_matrix(),
            risk_heatmap(),
            no_custody_safety_layer(),
        audit_log_panel(),
        spacing="4",
        width="100%",
    ))
