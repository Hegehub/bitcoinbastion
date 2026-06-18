from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card


def proof_packet_viewer(report_id: str = "Route report id") -> rx.Component:
    return card(
        trace_safety_banner(),
        alert("Proof packet is not available for this report.", "warning"),
        rx.text("This may require enterprise access or a backend endpoint not yet exposed."),
        rx.text("No placeholder hashes or fabricated packet metadata are shown."),
        rx.link("Back to Trace report", href=f"/trace/{report_id}"),
        title="Proof packet",
        subtitle=(
            "Evidence packet metadata, source lists, fingerprints, and timestamps "
            "appear only when provided by the backend."
        ),
        variant="evidence",
    )
