from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

PROOF_STATES = ("unsigned proof packet", "signed proof packet", "preview proof packet", "unavailable proof packet")


def proof_packet_explorer(packet: dict[str, Any] | None = None) -> rx.Component:
    state = str(packet.get("state", "unavailable proof packet")) if packet else "unavailable proof packet"
    return wow_card("Proof Packet Explorer", f"state: {state}", "packet id · report id · evidence refs · hash trail · redaction status · advisory flags · generated at · limitations", "This is not legal proof.")
