from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.evidence_state import EvidenceState


def proof_packet_actions() -> rx.Component:
    return card(
        rx.link("Back to Trace Report", href="/trace/" + EvidenceState.evidence_report_id),
        rx.link("Open Evidence Overview", href="/evidence"),
        rx.text("Refresh actions will call backend APIs only; no export action is shown here."),
        title="Actions",
    )
