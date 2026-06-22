from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card

REQUIRED_SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files "
    "or signing material."
)
SECURITY_WARNING = (
    "Never enter seed phrases, private keys, wallet files, keystores, xprv, yprv, zprv, "
    "or signing material into Bitcoin Bastion."
)


def safety_section() -> rx.Component:
    return card(rx.text(REQUIRED_SAFETY_COPY), title="No-custody safety model", variant="safety")
