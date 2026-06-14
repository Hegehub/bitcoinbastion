from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card

DOMAINS: tuple[tuple[str, str], ...] = (
    ("Public API", "/api/v1/public/status — read-oriented, deployment-specific limits may apply."),
    ("Trace API", "/api/v1/trace — public address context; authentication may apply."),
    ("Evidence API", "/api/v1/evidence — evidence references; read/write risk depends on endpoint."),
    ("Signals API", "/api/v1/signals/latest — read-oriented preview."),
    ("Market Intelligence API", "/api/v1/market/providers/health — provider state."),
    ("On-chain API", "/api/v1/onchain — public data context only."),
    ("Treasury API", "/api/v1/treasury — high risk; no UI execution here."),
    ("Policy API", "/api/v1/policy — advisory policy context."),
    ("Provider Health / Observability API", "/api/v1/health/providers — read-oriented."),
    ("Webhooks API", "/api/v1/webhooks — deployment configuration required."),
    ("WebSocket API", "/ws — streaming expectations depend on deployment."),
)


def api_explorer_panel() -> rx.Component:
    return cast(rx.Component, rx.vstack(
        rx.text("API Explorer is documentation-oriented. It does not execute risky actions. Endpoints may require authentication, rate limits, or deployment-specific configuration."),
        rx.grid(*[preview_card(name, desc) for name, desc in DOMAINS], columns="2", spacing="4", width="100%"),
        width="100%",
        spacing="4",
    ))
