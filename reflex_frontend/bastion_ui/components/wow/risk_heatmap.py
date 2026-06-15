from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

DIMS = ("Trace", "Evidence", "Provider Health", "Market Intelligence", "Treasury", "Policy", "Runtime", "Audit")


def risk_heatmap() -> rx.Component:
    return wow_card("Risk Heatmap", *[f"{dim}: unknown" for dim in DIMS], "Risk values: low · moderate · elevated · high · unknown")
