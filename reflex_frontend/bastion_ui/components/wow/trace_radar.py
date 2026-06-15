from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.wow._shared import summarize, wow_card

AXES = ("risk band", "privacy exposure", "origin confidence", "provider disagreement", "source quality", "freshness", "manual review need")


def trace_radar(data: dict[str, Any] | None = None) -> rx.Component:
    lines = [f"{axis}: {summarize(data, axis.replace(' ', '_'), 'Insufficient evidence')}" for axis in AXES]
    lines.append("Advisory-only. Insufficient evidence must remain visible when backend summary data is missing.")
    return wow_card("Trace Radar", *lines)
