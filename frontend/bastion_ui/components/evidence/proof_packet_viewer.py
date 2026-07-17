from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.evidence.degraded_evidence_banner import degraded_evidence_banner
from bastion_ui.components.evidence.evidence_chain import evidence_chain
from bastion_ui.components.evidence.evidence_limitations_card import evidence_limitations_card
from bastion_ui.components.evidence.proof_packet_actions import proof_packet_actions
from bastion_ui.components.evidence.proof_packet_card import proof_packet_card
from bastion_ui.components.evidence.source_disagreement_panel import source_disagreement_panel
from bastion_ui.components.ui.safety_banner import safety_banner
from bastion_ui.state.evidence_state import EvidenceState


def proof_packet_viewer() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            safety_banner("advisory"),
            rx.cond(EvidenceState.degraded_evidence_visible, degraded_evidence_banner()),
            proof_packet_card(),
            source_disagreement_panel(),
            evidence_chain(),
            evidence_limitations_card(),
            proof_packet_actions(),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
