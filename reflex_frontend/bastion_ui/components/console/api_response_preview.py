from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def api_response_preview() -> rx.Component:
    return card(
        rx.text("Example response preview is sanitized and illustrative."),
        rx.text('{"data": {"status": "unknown"}, "error": null}'),
        title="Response preview",
        subtitle="No secrets, credentials, or signing material are accepted.",
        variant="console",
    )
