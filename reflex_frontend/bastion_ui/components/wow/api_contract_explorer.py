from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

GROUPS = ("Public", "Trace", "Evidence", "Market", "Signals", "On-chain", "Treasury", "Policy", "Webhooks", "WebSocket")


def api_contract_explorer() -> rx.Component:
    return wow_card("API Contract Explorer", *[f"{group}: method/path/status planned or preview unless confirmed by backend; auth requirement and safety notes visible" for group in GROUPS])
