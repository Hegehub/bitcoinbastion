from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

TRACE_SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or "
    "signing material."
)


def trace_safety_banner() -> rx.Component:
    return alert(TRACE_SAFETY_COPY, "advisory")
