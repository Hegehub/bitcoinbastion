from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card


def audit_log_preview() -> rx.Component:
    return cast(rx.Component, rx.grid(
        preview_card("Recent events placeholder", "Audit Log preview is informational."),
        preview_card("Operator actions placeholder", "Immutability depends on deployment-level storage controls."),
        preview_card("Evidence replay placeholder", "Application-level audit logs are not WORM storage by themselves."),
        preview_card("Webhook delivery placeholder", "Delivery failures and degraded events remain visible."),
        preview_card("Failure events placeholder", "Fallback and unavailable states are not hidden."),
        columns="2",
        spacing="4",
        width="100%",
    ))
