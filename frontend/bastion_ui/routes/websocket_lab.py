from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import public_page
from bastion_ui.state.websocket_lab_state import WebSocketLabState


def websocket_lab_page() -> rx.Component:
    return public_page(
        "WebSocket contract laboratory",
        rx.callout(
            "Development/test laboratory — fixtures are always DEMO_FIXTURE.",
            role="status",
            color_scheme="orange",
        ),
        rx.hstack(
            rx.button(
                "Connect live provider health",
                on_click=WebSocketLabState.connect_provider_health,
                id="ws-connect",
            ),
            rx.button("Disconnect", on_click=WebSocketLabState.disconnect, id="ws-disconnect"),
            rx.button(
                "Test unsupported version",
                on_click=WebSocketLabState.demo_unsupported_version,
                id="ws-unsupported",
            ),
        ),
        rx.text(
            "Connection: ", WebSocketLabState.connection_status, id="ws-connection", role="status"
        ),
        rx.text("Stream: ", WebSocketLabState.stream, id="ws-stream"),
        rx.text("Wire version: ", WebSocketLabState.wire_version, id="ws-version"),
        rx.text("Message: ", WebSocketLabState.message, id="ws-message"),
        rx.text("Provenance: ", WebSocketLabState.provenance, id="ws-provenance"),
        rx.text(WebSocketLabState.safe_error, id="ws-error", role="alert"),
        subtitle=(
            "Strict backend-owned frames only; production unavailability never activates fixtures."
        ),
    )
