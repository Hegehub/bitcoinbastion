from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.grid_node_card import grid_node_card
from bastion_ui.components.console.sovereignty_score_card import sovereignty_score_card
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card

SOVEREIGN_GRID_SAFETY_COPY = (
    "Sovereign Grid is a frontend readiness view only. "
    "It does not create distributed backend mesh, "
    "mining support, custody, wallet control, or fake network status."
)


def sovereign_grid_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Sovereign Grid", size="6"),
            rx.text("System-readiness and sovereignty posture dashboard for operators."),
            card(
                rx.text(SOVEREIGN_GRID_SAFETY_COPY),
                title="Sovereign Grid limitations",
                variant="safety",
            ),
            degraded_state_banner(),
            responsive_grid(
                sovereignty_score_card(),
                grid_node_card(
                    "Runtime profile",
                    (
                        "Runtime profile metadata is unavailable until a sanitized "
                        "backend endpoint exists."
                    ),
                ),
                grid_node_card(
                    "Provider independence",
                    "Provider independence status is unknown without provider health data.",
                ),
                grid_node_card(
                    "Evidence readiness",
                    "Evidence readiness is pending global evidence health endpoints.",
                ),
                grid_node_card(
                    "No-custody posture",
                    "Console does not request wallet secrets or hold funds.",
                    "info",
                ),
                grid_node_card(
                    "Deployment posture",
                    (
                        "Deployment posture is unknown until public status exposes "
                        "sanitized runtime state."
                    ),
                ),
            ),
            card(
                rx.text(
                    "Operator checklist: verify runtime, providers, evidence, backups, "
                    "and degraded-state visibility."
                ),
                rx.text(
                    "Future backend endpoint needed: sanitized runtime profile "
                    "and readiness metadata."
                ),
                title="Operator control checklist",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
