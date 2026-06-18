from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.status_summary import STATUS_FALLBACK_COPY, status_summary
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page

STATUS_API_ENDPOINT = "/api/v1/public/status"


def status_page() -> rx.Component:
    return public_page(
        public_hero(
            "Public status and degraded-state visibility",
            "Status surfaces must show unavailable, stale, fallback, and degraded states instead "
            "of hiding uncertainty.",
            primary_label="Refresh later",
            primary_href="/status",
            secondary_label="Roadmap",
            secondary_href="/roadmap",
        ),
        status_summary(),
        section(
            card(
                alert(STATUS_FALLBACK_COPY, "stale"),
                rx.text(f"API dependency: {STATUS_API_ENDPOINT}"),
                rx.text("No live status is faked by the Reflex static route."),
                title="Backend health/status summary",
            ),
            title="Fallback behavior",
        ),
    )
