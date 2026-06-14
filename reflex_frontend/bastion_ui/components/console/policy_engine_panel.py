from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card


def policy_engine_panel() -> rx.Component:
    return cast(rx.Component, rx.grid(
        preview_card("Policy profile preview", "Policy Engine output is advisory until reviewed by an operator."),
        preview_card("Warning/event preview", "Risk events require operator review."),
        preview_card("Risk action review placeholder", "No treasury approval or irreversible mutation is exposed."),
        preview_card("Human Confirmation Firewall", "Risky actions require explicit human confirmation."),
        preview_card("Policy simulator placeholder", "Read, preview, explain, and local UI simulation only."),
        columns="2",
        spacing="4",
        width="100%",
    ))
