from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.audit_log_panel import audit_log_panel
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.ui.safety_banner import safety_banner


def console_page() -> rx.Component:
    return dashboard_shell("Bastion Console", rx.vstack(
        rx.text("Operator-facing command center. Display-only in this prompt; no execution controls, custody controls, or signing controls are exposed."),
        safety_banner("console"),
        audit_log_panel(),
        spacing="4",
        width="100%",
    ))
