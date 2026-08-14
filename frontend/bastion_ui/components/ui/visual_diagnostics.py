"""Safe development-only Feature-51 material diagnostics."""

from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.theme.tokens import MaterialLevel


def visual_diagnostics() -> rx.Component:
    return card(
        rx.text("Material tiers: " + ", ".join(level.value for level in MaterialLevel)),
        rx.text("Transparency fallback: matte; motion fallback: static"),
        rx.text("Contrast validation: primary ≥ 7:1; secondary ≥ 4.5:1"),
        title="Visual-system diagnostics",
        subtitle=("Development metadata only; no session, Access, proof, or private identifiers."),
        variant="matte",
    )
