from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.evidence.degraded_evidence_banner import degraded_evidence_banner
from bastion_ui.components.evidence.evidence_limitations_card import evidence_limitations_card
from bastion_ui.components.evidence.proof_packet_actions import proof_packet_actions
from bastion_ui.components.evidence.proof_packet_card import proof_packet_card
from bastion_ui.components.evidence.source_disagreement_panel import source_disagreement_panel
from bastion_ui.components.ui.error_state import error_state
from bastion_ui.components.ui.loading_state import loading_state
from bastion_ui.components.ui.safety_banner import safety_banner


def proof_packet_viewer(report_id: str = "Route report id") -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            safety_banner("advisory"),
            degraded_evidence_banner(),
            loading_state("Loading Proof Packet when backend data is available…"),
            error_state(
                "Proof Packet unavailable. This endpoint may not be exposed for this report."
            ),
            proof_packet_card(),
            source_disagreement_panel(),
            evidence_limitations_card(),
            proof_packet_actions(report_id),
            align="stretch",
            spacing="4",
            width="100%",
        ),
    )
