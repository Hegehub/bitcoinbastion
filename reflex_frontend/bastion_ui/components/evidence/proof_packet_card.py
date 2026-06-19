from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.evidence.evidence_chain import evidence_chain
from bastion_ui.components.ui.card import card


def proof_packet_card(packet: dict[str, Any] | None = None) -> rx.Component:
    payload = packet or {}
    items = payload.get("evidence_items") if isinstance(payload.get("evidence_items"), list) else []
    return card(
        rx.text("Packet status: " + str(payload.get("status") or "Proof Packet unavailable")),
        rx.text("Generated: " + str(payload.get("generated_at") or "Not available")),
        evidence_chain(items),
        title="Proof Packet contents",
        subtitle="Only backend-provided fields are displayed.",
        variant="evidence",
    )
