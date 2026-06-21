from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.proof_packet_viewer import proof_packet_viewer
from bastion_ui.routes._shared import public_page


def trace_proof_packet_page() -> rx.Component:
    return public_page(
        "Trace proof packet",
        proof_packet_viewer(),
        subtitle="Proof Packet availability depends on backend endpoint access.",
    )
