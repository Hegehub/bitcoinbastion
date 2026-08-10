from __future__ import annotations

import reflex as rx

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.components.public.status_summary import status_fallback_card
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page
from bastion_ui.state.prompt2_status_state import Prompt2StatusState


def _canonical_status_harness() -> rx.Component:
    return card(
        rx.hstack(
            rx.button(
                "Load live status",
                on_click=Prompt2StatusState.load_status,
                id="status-load",
            ),
            rx.button(
                "Cancel",
                on_click=Prompt2StatusState.cancel_status,
                variant="outline",
                id="status-cancel",
            ),
        ),
        rx.text("Request state: ", Prompt2StatusState.lifecycle, id="status-lifecycle"),
        rx.cond(
            Prompt2StatusState.view_model,
            rx.vstack(
                rx.text(
                    "Platform status: ",
                    Prompt2StatusState.platform_status,
                    id="status-platform",
                ),
                rx.text(
                    "Trace status: ",
                    Prompt2StatusState.trace_status,
                    id="status-trace",
                ),
                rx.text(
                    "Last backend update: ",
                    Prompt2StatusState.last_update,
                    id="status-updated",
                ),
                provenance_badge(
                    Prompt2StatusState.provenance_state,
                    source=Prompt2StatusState.provenance_source,
                    details=Prompt2StatusState.provenance_details,
                ),
                align="start",
            ),
            rx.text(Prompt2StatusState.safe_error, role="alert", id="status-error"),
        ),
        title="Canonical typed status harness",
    )


def status_page() -> rx.Component:
    return public_page(
        "Status",
        _canonical_status_harness(),
        status_fallback_card(),
        card(
            rx.text(
                "Provider health and degraded-mode signals should be displayed when "
                "backend data is available."
            ),
            rx.text(
                "Timestamp and stale-data notices must remain visible when freshness is uncertain."
            ),
            title="Provider health and degraded mode",
        ),
        subtitle=(
            "Public status route using safe fallback behavior when live API data is unavailable."
        ),
    )
