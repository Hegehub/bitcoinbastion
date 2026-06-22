from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.evidence_state import EvidenceState


def proof_packet_card() -> rx.Component:
    return card(
        rx.text("Report id: ", EvidenceState.evidence_report_id),
        rx.text("Packet status: ", EvidenceState.proof_packet_status),
        rx.text("Generated: ", EvidenceState.last_updated),
        rx.text("Source list: shown only when backend data includes sources."),
        rx.text("Evidence items: shown only when backend data includes items."),
        title="Proof Packet status",
        variant="evidence",
    )
