from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
from bastion_ui.components.wow.proof_packet_explorer import proof_packet_explorer
from bastion_ui.components.wow.operator_audit_replay import operator_audit_replay
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.ui.card import card


def console_evidence_page() -> rx.Component:
    return dashboard_shell("Console Evidence", rx.vstack(
        evidence_chain_viewer(),
        proof_packet_explorer(),
        operator_audit_replay(),
        card(rx.text("Evidence chain placeholder. No fake data is generated."), title="Evidence Chain"),
        card(rx.text("Proof Packet placeholder. Unavailable evidence is not hidden."), title="Proof Packet"),
        card(rx.text("Replay and audit placeholder. Backend evidence is required for live data."), title="Replay and Audit"),
        spacing="4",
        width="100%",
    ))
