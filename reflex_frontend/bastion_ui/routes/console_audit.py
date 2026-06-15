from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.operator_audit_replay import operator_audit_replay
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
from bastion_ui.components.wow.api_contract_explorer import api_contract_explorer
from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.audit_log_preview import audit_log_preview
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_audit_page() -> rx.Component:
    return dashboard_shell(
        "Audit Log",
        rx.vstack(
            console_page_header("Audit Log", "Audit Log preview is informational. Immutability depends on deployment-level storage controls. Application-level audit logs are not WORM storage by themselves."),
            console_status_strip(),
            operator_audit_replay(),
            evidence_chain_viewer(),
            api_contract_explorer(),
            audit_log_preview(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
