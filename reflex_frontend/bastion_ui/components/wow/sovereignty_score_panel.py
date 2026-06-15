from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

FACTORS = ("self-hosted status", "no-custody status", "own-node readiness", "provider dependency", "degraded-mode visibility", "evidence/replay availability", "operator confirmation policy", "runtime portability")


def sovereignty_score_panel() -> rx.Component:
    return wow_card("Sovereignty Score Panel", "Operational posture, not financial or legal score.", *[f"{factor}: unknown" for factor in FACTORS])
