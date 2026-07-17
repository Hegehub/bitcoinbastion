from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.audit_log_panel import audit_log_panel
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.wow.audit_replay_timeline import audit_replay_timeline


def console_audit_page() -> rx.Component:
    return dashboard_shell(audit_log_panel(), audit_replay_timeline())
