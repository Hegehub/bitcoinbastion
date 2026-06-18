from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.proof_packet_viewer import proof_packet_viewer
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.routes._public import public_page


def trace_proof_packet_page() -> rx.Component:
    return public_page(
        proof_packet_viewer(),
        trace_limitations_card(),
    )
