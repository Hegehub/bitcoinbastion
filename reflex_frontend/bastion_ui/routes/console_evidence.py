from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.evidence_console_panel import evidence_console_panel


def console_evidence_page() -> rx.Component:
    return dashboard_shell(evidence_console_panel())
