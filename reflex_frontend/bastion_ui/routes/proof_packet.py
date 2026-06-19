from __future__ import annotations

import reflex as rx

from bastion_ui.components.evidence.proof_packet_viewer import proof_packet_viewer
from bastion_ui.routes._public import public_page


def trace_proof_packet_page() -> rx.Component:
    return public_page(proof_packet_viewer())
