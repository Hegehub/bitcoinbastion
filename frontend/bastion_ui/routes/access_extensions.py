# ruff: noqa: E501
from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page


def business_access_page() -> rx.Component:
    return public_page(
        "Business access",
        card(
            rx.text("Owner · Admin · Operator · Cashier · Analyst · Viewer · Device · Bot"),
            rx.text(
                "These labels never grant permission. Effective capabilities and quorum are loaded from backend policy responses."
            ),
            title="Effective business roles",
        ),
        subtitle="Critical role changes require backend-mandated wallet/LNURL step-up or quorum.",
    )


def business_devices_page() -> rx.Component:
    return public_page(
        "Business devices",
        card(
            rx.text("PayRegister, Vault, bot, and operator device status is backend-provided."),
            title="Business Device Binding",
        ),
        subtitle="Private keys and sensitive wallet identifiers are never displayed.",
    )


def business_security_page() -> rx.Component:
    return public_page(
        "Business security",
        card(
            rx.text(
                "Pending quorum · approved pseudonyms · required approval count · policy status"
            ),
            title="Multi-method quorum",
        ),
        subtitle="Frontend role hiding is not security.",
    )


def register_access_page() -> rx.Component:
    return public_page(
        "PayRegister access",
        card(
            rx.text(
                "PayRegister payment/refund capabilities require effective backend role and policy approval."
            ),
            title="Register access policy",
        ),
        subtitle="Cashier metadata is context, never authorization.",
    )


def register_devices_page() -> rx.Component:
    return public_page(
        "PayRegister devices",
        card(
            rx.text("Store · terminal · status · risk · last seen · Device Binding"),
            title="Register devices",
        ),
        subtitle="Device keys remain private and cannot be viewed here.",
    )


def register_refunds_page() -> rx.Component:
    return public_page(
        "PayRegister refunds",
        card(
            rx.text(
                "Invoice/order · amount · merchant · terminal · reason · policy · step-up requirement"
            ),
            rx.text("LNURL-withdraw is generated only after backend policy approval."),
            title="Policy-gated refund",
            variant="safety",
        ),
        subtitle="Cashier limits cannot be bypassed by frontend controls.",
    )
