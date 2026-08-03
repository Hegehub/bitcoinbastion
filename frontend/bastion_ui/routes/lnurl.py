# ruff: noqa: E501
from __future__ import annotations

import reflex as rx

from bastion_ui.components.auth import (
    lightning_address_card,
    lnurl_auth_qr_code,
    lnurl_payment_status,
)
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page


def lnurl_auth_page() -> rx.Component:
    return public_page(
        "LNURL-auth",
        lnurl_auth_qr_code(),
        card(
            rx.text(
                "The implemented backend does not expose an auth-attempt status route. Polling is unavailable until that contract exists; no success is inferred locally."
            ),
            title="Backend contract gap",
            variant="safety",
        ),
        subtitle="Lightning-wallet proof is not on-chain ownership proof or unrestricted authorization.",
    )


def lnurl_pay_page() -> rx.Component:
    return public_page(
        "LNURL-pay",
        lnurl_payment_status(),
        lightning_address_card(),
        subtitle="External wallet payment; backend settlement and entitlement issuance remain authoritative.",
    )


def lnurl_payment_status_page() -> rx.Component:
    return public_page(
        "LNURL payment verification",
        lnurl_payment_status(),
        responsive_grid(
            *(
                card(rx.text(state), title="Payment state")
                for state in (
                    "creating_payment",
                    "waiting_for_wallet",
                    "invoice_issued",
                    "payment_pending",
                    "verifying",
                    "settled",
                    "activating_entitlement",
                    "active",
                    "expired",
                    "failed",
                )
            )
        ),
        subtitle="Status does not rely on color and can be announced to assistive technology.",
    )
