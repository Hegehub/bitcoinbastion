from __future__ import annotations

import reflex as rx

from bastion_ui.components.safety.advisory_notice import advisory_notice
from bastion_ui.components.safety.no_custody_notice import no_custody_notice
from bastion_ui.components.safety.safety_banner import trace_safety_banner
from bastion_ui.components.ui.card import card

REQUIRED_PUBLIC_SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or "
    "signing material."
)

SECURITY_WARNING = (
    "Never enter seed phrases, private keys, wallet files, keystores, xprv, yprv, zprv, or "
    "signing material into Bitcoin Bastion."
)


def safety_section() -> rx.Component:
    return card(
        rx.text(REQUIRED_PUBLIC_SAFETY_COPY, weight="bold"),
        advisory_notice(),
        no_custody_notice(),
        trace_safety_banner(),
        title="No-custody safety model",
        variant="safety",
    )
