from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card


def deployment_status_panel() -> rx.Component:
    return cast(rx.Component, rx.grid(
        preview_card("Runtime profile summary", "Deployment status is evidence-driven."),
        preview_card("Kubernetes/Compose/Systemd", "A rendered manifest is not proof of production readiness."),
        preview_card("Migration status placeholder", "Migration evidence is required."),
        preview_card("Evidence artifact status", "Production readiness requires environment-specific evidence artifacts."),
        preview_card("Provider health status", "Provider failures are not hidden."),
        preview_card("Readiness blockers", "Blockers remain visible until evidence closes them."),
        columns="2",
        spacing="4",
        width="100%",
    ))
