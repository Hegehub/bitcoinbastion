from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def security_page() -> rx.Component:
    return page_shell("Security", "No-custody boundaries and explicit limitations are product requirements.", (
        ("No custody", "Bitcoin Bastion is not a wallet or custodian."),
        ("No private keys", "Do not enter private keys or signing material."),
        ("No seed phrases", "Do not enter seed phrases or mnemonic material."),
        ("No wallet files", "Do not upload wallet files or keystores."),
        ("Human confirmation firewall", "Risky actions require explicit operator awareness and approval."),
        ("Signed webhooks", "Signed webhook hardening is planned or implementation-specific; do not assume production readiness."),
        ("Explicit degraded state", "Fallback, stale, degraded, and unavailable states must remain visible."),
        ("Security review", "Rate limiting and production security review remain required where applicable."),
    ))
