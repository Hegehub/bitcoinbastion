from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def evidence_chain_viewer(rows: list[dict[str, Any]] | None = None) -> rx.Component:
    if not rows:
        return wow_card("Evidence Chain Viewer", "No evidence chain available yet.", "Limitations and replay availability remain visible.")
    return wow_card("Evidence Chain Viewer", *[str(row) for row in rows], "source entity · derived finding · confidence · limitation · replay · hash · review state")
