from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.api_endpoint_card import api_endpoint_card
from bastion_ui.components.console.api_response_preview import api_response_preview
from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card

API_EXPLORER_SAFETY_COPY = (
    "API Explorer is for inspection and safe read-only calls. Risky actions require explicit "
    "operator approval. Never submit seed phrases, private keys, wallet files or signing material."
)


def api_explorer_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("API Explorer", size="6"),
            rx.text("Inspect Bitcoin Bastion API capabilities and safe read-only examples."),
            card(rx.text(API_EXPLORER_SAFETY_COPY), title="API Explorer safety", variant="safety"),
            degraded_state_banner(),
            responsive_grid(
                api_endpoint_card("GET /api/v1/public/status", "Public", "Safe read"),
                api_endpoint_card("GET /api/v1/public/roadmap", "Public", "Safe read"),
                api_endpoint_card("GET /api/v1/public/features", "Public", "Safe read"),
                api_endpoint_card("GET /api/v1/signals/top", "Signals", "Safe read"),
                api_endpoint_card(
                    "GET /api/v1/public/trace/{report_id}/summary", "Trace", "Safe read"
                ),
                api_endpoint_card("POST /api/v1/treasury/drafts", "Treasury", "Draft-only"),
                api_endpoint_card(
                    "PATCH /api/v1/policy/rules/{rule_id}", "Policy", "Requires approval"
                ),
                api_endpoint_card("POST /api/v1/webhooks/secrets", "Webhooks", "Admin-only"),
            ),
            api_response_preview(),
            card(
                rx.text(
                    "Categories covered: Public, Trace, Evidence, Signals, Market, "
                    "On-chain, Treasury, Policy, Provider Health, Webhooks, WebSocket."
                ),
                rx.text("Only Safe read endpoint cards are marked tryable."),
                title="Explorer notes",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
