from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.audit_log_panel import audit_log_panel
from bastion_ui.components.console.dashboard_shell import dashboard_shell


def console_audit_page() -> rx.Component:
    return dashboard_shell(audit_log_panel())
