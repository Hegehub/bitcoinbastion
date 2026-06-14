from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def developers_page() -> rx.Component:
    return page_shell("Developers", "API-first, no-custody development surfaces for Bitcoin Bastion.", (
        ("API-first architecture", "OpenAPI-oriented development keeps the backend contract authoritative."),
        ("Event-driven preparation", "Developer layer is being prepared through event-driven APIs, signed webhooks, WebSocket streams, SDKs, and CLI tooling."),
        ("Future webhooks", "Webhook work must be signed, replay-safe, and explicit about delivery limitations."),
        ("Future WebSocket streams", "Streams must preserve degraded, fallback, and stale state visibility."),
        ("Future SDK", "SDKs should wrap backend APIs without duplicating backend calculations."),
        ("No-custody API posture", "APIs must not request seed phrases, private keys, wallet files, or signing material."),
    ))
