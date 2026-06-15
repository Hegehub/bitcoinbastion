from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def policy_engine_simulator() -> rx.Component:
    return wow_card("Policy Engine Simulator", "Simulation only.", "selected policy profile: preview", "sample condition: static preview", "expected warning: operator review", "expected block/review result: review required", "No backend policy mutation or auto-execution.")
