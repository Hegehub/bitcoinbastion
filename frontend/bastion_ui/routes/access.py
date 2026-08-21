# ruff: noqa: E501
from __future__ import annotations

import reflex as rx

from bastion_ui.components.auth import (
    dedicated_auth_address_notice,
    lightning_address_card,
    lnurl_payment_status,
    wallet_auth_method_selector,
    wallet_security_warning,
)
from bastion_ui.components.layout.grid import responsive_grid, three_column_grid
from bastion_ui.components.ui.card import card
from bastion_ui.domain.access.models import AccessOfferViewModel
from bastion_ui.routes._shared import link_card, public_page
from bastion_ui.state.access_acquisition_state import AccessAcquisitionState


def _offer_card(offer: AccessOfferViewModel) -> rx.Component:
    return card(
        rx.text(offer.capability, weight="bold"),
        rx.text(offer.amount_sats, " ", offer.price_unit),
        rx.text(offer.duration_days, " days"),
        rx.text("Terms: ", offer.terms_version),
        rx.text("Revision: ", offer.revision_id, overflow_wrap="anywhere"),
        rx.text("Scopes: ", offer.scopes.to_string(), overflow_wrap="anywhere"),
        rx.foreach(offer.limitations, lambda limitation: rx.text(limitation)),
        rx.button(
            "Select this Offer",
            on_click=AccessAcquisitionState.select_offer(offer.offer_id),
            aria_label="Select backend Offer " + offer.capability,
        ),
        title="Backend Access Offer",
    )


def access_page() -> rx.Component:
    return public_page(
        "Bitcoin Bastion Access",
        rx.text(
            "Choose a wallet proof method. Payment, wallet proof, and LNURL-auth are distinct events; protected access requires a Device-bound PoP Session and backend policy approval."
        ),
        rx.text("This is not a password."),
        rx.text("Bastion will never ask for your Bitcoin seed or private key."),
        wallet_auth_method_selector(),
        three_column_grid(
            link_card(
                "Subscription plans",
                "/access/plans",
                "Choose a backend-supported plan and pay externally with LNURL-pay.",
            ),
            link_card(
                "Access Certificate",
                "/access/certificate",
                "Optional high-assurance bridge; never a bearer password.",
            ),
            link_card(
                "Business / Enterprise",
                "/business/access",
                "Deployment capabilities and roles remain backend-defined.",
            ),
        ),
        wallet_security_warning(),
        dedicated_auth_address_notice(),
        subtitle="Wallet-first is not wallet-only. LNURL-native is not LNURL-only.",
    )


def access_plans_page() -> rx.Component:
    return public_page(
        "Subscription plans",
        rx.cond(
            AccessAcquisitionState.offer_status == "loading",
            rx.text("Loading authoritative Access Offers…", role="status"),
            rx.cond(
                AccessAcquisitionState.offers.length() > 0,
                responsive_grid(rx.foreach(AccessAcquisitionState.offers, _offer_card)),
                card(
                    rx.text(
                        "Access Offers are unavailable. No placeholder pricing or capability was substituted.",
                        role="alert",
                    ),
                    title="Offers unavailable",
                    variant="safety",
                ),
            ),
        ),
        rx.cond(
            AccessAcquisitionState.selected_offer_id != "",
            rx.button(
                "Create Checkout",
                on_click=AccessAcquisitionState.create_checkout,
                disabled=AccessAcquisitionState.checkout_in_flight,
                aria_label="Create one Checkout from the selected backend Offer",
            ),
        ),
        card(
            rx.text(
                "Sovereign Security Mode is a high-assurance policy mode, not a simple subscription tier."
            ),
            title="High assurance",
        ),
        subtitle="The backend entitlement and Policy Engine—not the plan label in this page—determine access.",
    )


def access_checkout_page() -> rx.Component:
    return public_page(
        "Access Checkout",
        rx.cond(
            AccessAcquisitionState.checkout,
            card(
                rx.text("Capability: ", AccessAcquisitionState.checkout.capability),
                rx.text(
                    "Frozen price: ", AccessAcquisitionState.checkout.amount_sats,
                    " ", AccessAcquisitionState.checkout.price_unit,
                ),
                rx.text("Frozen duration: ", AccessAcquisitionState.checkout.duration_days, " days"),
                rx.text("Offer revision: ", AccessAcquisitionState.checkout.offer_revision_id),
                rx.text("Terms: ", AccessAcquisitionState.checkout.terms_version),
                rx.text(
                    "Scopes: ",
                    AccessAcquisitionState.checkout.scopes.to_string(),
                    overflow_wrap="anywhere",
                ),
                rx.text("Status: ", AccessAcquisitionState.checkout.status, role="status"),
                rx.text(
                    "Issuance eligibility: ", AccessAcquisitionState.checkout.eligibility_reason,
                    role="status",
                ),
                title="Frozen Checkout terms",
                subtitle="These values come from the Checkout snapshot, not the current Offer list.",
            ),
            rx.text("Loading Checkout…", role="status"),
        ),
        card(
            rx.text(
                "Issuance proves possession of this browser device's non-extractable Access key. "
                "It does not prove legal identity or payment by itself."
            ),
            rx.cond(
                AccessAcquisitionState.checkout & AccessAcquisitionState.checkout.issuance_eligible,
                rx.button(
                    "Verify device and issue Access",
                    on_click=AccessAcquisitionState.begin_secure_issuance,
                    disabled=AccessAcquisitionState.challenge_in_flight
                    | AccessAcquisitionState.issuance_in_flight,
                    aria_label="Verify this device key and issue Access once",
                ),
                rx.text("Issuance is unavailable until the backend marks Checkout eligible."),
            ),
            rx.text("Device security: ", AccessAcquisitionState.security_status, role="status"),
            rx.text("Issuance: ", AccessAcquisitionState.issuance_status, role="status"),
            rx.cond(
                AccessAcquisitionState.safe_error != "",
                rx.text(AccessAcquisitionState.safe_error, role="alert"),
            ),
            title="Device-key possession verification",
        ),
        subtitle="Payment and eligibility remain backend-owned. No private key leaves the secure provider.",
    )


def access_payment_page() -> rx.Component:
    return public_page(
        "Payment preparation",
        lightning_address_card(),
        lnurl_payment_status(),
        subtitle="Payment is not authentication.",
    )


def access_payment_pending_page() -> rx.Component:
    return public_page(
        "Payment pending",
        lnurl_payment_status(),
        card(
            rx.text("Re-check settlement through Bastion. Do not rely on wallet UI success alone."),
            title="Backend verification required",
        ),
        subtitle="Status: invoice issued or payment pending—not active.",
    )


def access_success_page() -> rx.Component:
    return public_page(
        "Bastion Access issued",
        rx.cond(
            AccessAcquisitionState.issued_access,
            card(
                rx.text("Grant ID: ", AccessAcquisitionState.issued_access.grant_id),
                rx.text("Capability: ", AccessAcquisitionState.issued_access.capability),
                rx.text(
                    "Scopes: ",
                    AccessAcquisitionState.issued_access.scopes.to_string(),
                    overflow_wrap="anywhere",
                ),
                rx.text("Issued: ", AccessAcquisitionState.issued_access.issued_at.to_string()),
                rx.text("Expires: ", AccessAcquisitionState.issued_access.expires_at.to_string()),
                rx.text(
                    "Device binding: ",
                    AccessAcquisitionState.issued_access.device_key_fingerprint,
                    overflow_wrap="anywhere",
                ),
                rx.text("Status: ", AccessAcquisitionState.issued_access.status, role="status"),
                title="Authoritative issued Access",
                subtitle="This is a non-secret server-side Grant summary. No bearer token is displayed.",
            ),
            rx.text("Loading issued Access…", role="status"),
        ),
        rx.cond(
            AccessAcquisitionState.safe_error != "",
            rx.text(AccessAcquisitionState.safe_error, role="alert"),
        ),
        subtitle="Refresh and deep links read the existing Grant and never issue again.",
    )


def access_certificate_page() -> rx.Component:
    return public_page(
        "Access Certificate",
        card(
            rx.text(
                "Create, inspect, import bastion-pass.bbp, revoke, or export only when the deployment exposes the Access Certificate APIs."
            ),
            rx.text(
                "An Access Certificate is an additional Bastion security layer. It does not replace wallet proof, Device Binding, PoP Session, or Policy Engine."
            ),
            title="Optional high-assurance bridge",
        ),
        subtitle="Unavailable actions must remain visibly unavailable rather than producing mock success.",
    )


def access_offline_page() -> rx.Component:
    return public_page(
        "Offline validity",
        card(
            rx.text(
                "Valid until · allowed offline scopes · revocation epoch · Device Binding · issuer status"
            ),
            title="Offline Validity Pack",
            subtitle="Full offline administrator access is not implied.",
        ),
        subtitle="Optional and deployment-controlled.",
    )
