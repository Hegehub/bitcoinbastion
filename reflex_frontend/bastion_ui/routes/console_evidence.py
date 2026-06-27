from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.evidence_console_panel import evidence_console_panel
from bastion_ui.components.wow.audit_replay_timeline import audit_replay_timeline
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer


def console_evidence_page() -> rx.Component:
    return dashboard_shell(
        evidence_console_panel(), evidence_chain_viewer(), audit_replay_timeline()
    )
