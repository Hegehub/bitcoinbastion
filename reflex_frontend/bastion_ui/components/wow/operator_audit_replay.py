from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def operator_audit_replay(events: list[dict[str, Any]] | None = None) -> rx.Component:
    if not events:
        return wow_card("Operator Audit Replay", "No audit replay events available yet.", "timestamp · actor/system · action type · entity · result · evidence ref · limitation")
    return wow_card("Operator Audit Replay", *[str(event) for event in events])
