from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.trace_console_panel import trace_console_panel
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
from bastion_ui.components.wow.privacy_exposure_lens import privacy_exposure_lens
from bastion_ui.components.wow.trace_radar import trace_radar


def console_trace_page() -> rx.Component:
    return dashboard_shell(
        trace_console_panel(), trace_radar(), privacy_exposure_lens(), evidence_chain_viewer()
    )
