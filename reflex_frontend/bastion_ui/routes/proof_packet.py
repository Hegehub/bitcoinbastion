from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.trace.proof_packet_viewer import proof_packet_viewer
from bastion_ui.components.ui.safety_banner import safety_banner
from bastion_ui.state.trace_state import TraceState


def proof_packet_page() -> rx.Component:
    return public_layout(cast(rx.Component, rx.vstack(
        rx.heading("Proof Packet", size="7"),
        safety_banner("proof_packet"),
        proof_packet_viewer(TraceState.evidence),
        rx.text("Evidence references, hash/integrity fields, redaction flags, advisory flags, and limitations appear only when provided by the backend."),
        spacing="5",
        align="start",
        width="100%",
    )))
