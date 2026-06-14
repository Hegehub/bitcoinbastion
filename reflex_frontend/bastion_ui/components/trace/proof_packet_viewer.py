from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.card import safety_card


def proof_packet_viewer(evidence: list[dict[str, Any]] | None = None) -> rx.Component:
    return safety_card(
        rx.text("Proof Packet data is not available from the public API yet. This page is a frontend-ready placeholder and must not be treated as certified evidence."),
        rx.text("Hash/integrity, redaction, advisory, and limitations flags are shown when provided by the backend."),
        title="Proof Packet",
    )
