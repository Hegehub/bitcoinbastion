from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card

OPERATOR_SAFETY_COPY = (
    "Bitcoin Bastion is advisory-only. Do not enter seed phrases, private keys, "
    "xprv/yprv/zprv values, wallet files, keystores, or signing material. Trace "
    "and market intelligence outputs are not legal verification, not Bitcoin "
    "consensus proof, and not financial advice. Risky actions must remain "
    "review-based and require explicit human approval."
)


def operator_safety_panel() -> rx.Component:
    return card(
        rx.text(OPERATOR_SAFETY_COPY),
        title="Operator safety boundaries",
        subtitle="No custody, signing, or automatic execution is available from this shell.",
        variant="safety",
    )
