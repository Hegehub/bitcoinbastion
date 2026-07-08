# ruff: noqa: E501
from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid, three_column_grid
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import link_card, public_page

PLAN_CODES = (
    (
        "Lite",
        "lite_pass",
        "Entry access with basic metrics, one-device recovery, and no child keys.",
    ),
    (
        "Basic",
        "basic_pass",
        "Basic dashboards, 12-word Bastion Recovery Seed, and read-only limits.",
    ),
    (
        "Plus",
        "plus_pass",
        "Standard market and trace access, Telegram pairing, and limited delegation.",
    ),
    ("Pro", "pro_pass", "Historical queries, bot access, 10 child keys, and 2-of-3 recovery."),
    (
        "Business",
        "business_pass",
        "Workspace roles, PayRegister operator keys, cashier shifts, and audit trails.",
    ),
    (
        "Enterprise",
        "enterprise_pass",
        "Custom issuer policy, enterprise quorum, private limits, and approval hooks.",
    ),
)

ACCESS_SAFETY_COPY = (
    "This is not a password.",
    "This is not your Bitcoin wallet seed.",
    "Bastion will never ask for your Bitcoin wallet seed or private key.",
)


def _warning_block() -> rx.Component:
    return card(
        *(rx.text(line) for line in ACCESS_SAFETY_COPY),
        title="Access safety rules",
        subtitle="Proof-of-Access uses a pass plus device/session proof; never paste wallet secrets.",
        variant="safety",
    )


def access_page() -> rx.Component:
    return public_page(
        "Bastion Access",
        rx.text(
            "Select a plan, pay through the Access checkout, import your Bastion Access Pass, and create an origin-bound Proof-of-Possession session."
        ),
        responsive_grid(
            *(
                card(
                    rx.text(description),
                    rx.text(f"Plan code: {code}"),
                    rx.link("Start checkout", href=f"/access/checkout?plan={code}"),
                    title=name,
                )
                for name, code, description in PLAN_CODES
            )
        ),
        three_column_grid(
            link_card(
                "Import an Access Pass",
                "/access/import",
                "Create a challenge and session without storing the raw pass in browser localStorage.",
            ),
            link_card(
                "View Access status",
                "/access/me",
                "See plan, scopes, limits, session expiry, recovery status, and locked metric groups.",
            ),
            link_card(
                "Emergency lockdown",
                "/access/lockdown",
                "Freeze compromised sessions, child keys, and delegated passes while recovery remains available.",
            ),
        ),
        _warning_block(),
        subtitle="Accountless Proof-of-Access replaces login, register, passwords, and bearer tokens.",
    )


def access_checkout_page() -> rx.Component:
    states = (
        "idle",
        "creating_invoice",
        "waiting_for_payment",
        "payment_settled",
        "payment_expired",
        "payment_failed",
        "provider_unavailable",
        "degraded_mode",
    )
    return public_page(
        "Access checkout",
        card(
            rx.text(
                "Choose one of: lite_pass, basic_pass, plus_pass, pro_pass, business_pass, enterprise_pass."
            ),
            rx.text(
                "The UI calls POST /v1/access/payment-intents, then polls GET /v1/access/payment-intents/{payment_intent_id}."
            ),
            rx.text("Access Pass issuance is disabled until the backend reports payment_settled."),
            title="Bitcoin / Lightning payment intent",
        ),
        responsive_grid(*(card(rx.text(state), title="Checkout state") for state in states)),
        _warning_block(),
        subtitle="Invoices may be pending, expired, failed, unavailable, or degraded without exposing secrets.",
    )


def access_success_page() -> rx.Component:
    return public_page(
        "Access success",
        card(
            rx.text(
                "After settlement, call POST /v1/access/certificates to issue certificate metadata and the Bastion Access Pass."
            ),
            rx.text("Save this Bastion Access Pass now. It will be shown only once."),
            rx.text("Offer bastion-pass.bbp download when the backend returns an export payload."),
            rx.text(
                "Do not put the raw Access Pass in URLs, analytics, console logs, or localStorage."
            ),
            title="Show-once pass delivery",
            variant="safety",
        ),
        _warning_block(),
        subtitle="The success page never displays a pass before payment settlement.",
    )


def access_import_page() -> rx.Component:
    return public_page(
        "Import Bastion Access Pass",
        card(
            rx.text(
                "Import a raw Bastion Access Pass, bastion-pass.bbp file, or certificate payload when supported."
            ),
            rx.text(
                "Client-side validation rejects seed-like phrases, xprv/yprv/zprv material, WIF-like private keys, and wallet files."
            ),
            rx.text(
                "Create an origin-bound challenge for the current browser origin, then sign it with Vault or an approved device signer."
            ),
            rx.text(
                "Development signer — not for production. Production builds must keep ACCESS_DEV_SIGNER_ENABLED=false."
            ),
            title="Challenge and session flow",
        ),
        responsive_grid(
            card(
                rx.text("POST /v1/access/challenges"),
                rx.text("Origin-bound, scope-readable challenge."),
                title="1. Create challenge",
            ),
            card(
                rx.text("Vault/device signs challenge"),
                rx.text("Browser is not the root of trust."),
                title="2. Sign challenge",
            ),
            card(
                rx.text("POST /v1/access/sessions"),
                rx.text("Receive short-lived Proof-of-Possession session."),
                title="3. Create session",
            ),
        ),
        _warning_block(),
        subtitle="No password, mandatory email, wallet seed, or private-key auth field is provided.",
    )


def access_me_page() -> rx.Component:
    fields = (
        "current plan",
        "active scopes",
        "active metric groups",
        "locked metric groups",
        "quota usage",
        "request limits",
        "session expiry",
        "device fingerprint short display",
        "recovery status",
        "revocation status",
        "Access Integrity Score when available",
        "child API key and delegated pass counts",
    )
    return public_page(
        "Access status",
        responsive_grid(*(card(rx.text(field), title="Status field") for field in fields)),
        card(
            rx.text(
                "Dashboard/private pages must show locked, upgrade_required, expired, revoked, lockdown, or degraded states before requesting premium data."
            ),
            rx.text(
                "Never show raw pass_lookup_hash, raw session token, raw Access Pass, private key, full device key, or backend-only hashes."
            ),
            title="Safe status display",
            variant="safety",
        ),
        subtitle="Safe metadata for the active Proof-of-Access session.",
    )


def access_recovery_page() -> rx.Component:
    return public_page(
        "Access recovery",
        card(
            rx.text("This recovery phrase is for Bastion Access only."),
            rx.text("It is NOT your Bitcoin wallet seed."),
            rx.text("Never enter your Bitcoin wallet seed into Bastion."),
            rx.text(
                "Bastion cannot recover Pro, Business, or Enterprise access through support alone."
            ),
            title="Recovery safety copy",
            variant="safety",
        ),
        responsive_grid(
            card(
                rx.text(
                    "Lite / Basic / Plus: 12-word Bastion Recovery Seed with cooldown and status checks."
                ),
                title="12-word profiles",
            ),
            card(
                rx.text("Pro: 24-word Bastion Recovery Seed with required 2-of-3 recovery."),
                title="Pro quorum",
            ),
            card(
                rx.text(
                    "Business: Owner/Admin/Business Recovery Seed quorum; Enterprise: 3-of-5 ceremony."
                ),
                title="Business / Enterprise",
            ),
        ),
        card(
            rx.text(
                "Start, status, verify-factor, complete, and rotate actions call backend recovery endpoints only when available; the UI does not fake recovery success."
            ),
            title="Backend-bound recovery",
        ),
        subtitle="Recovery remains available when normal access is locked down.",
    )


def access_lockdown_page() -> rx.Component:
    return public_page(
        "Emergency lockdown",
        card(
            rx.text(
                "Lockdown is designed for suspected compromise. After lockdown, normal access may require recovery."
            ),
            rx.text(
                "Requires an active Proof-of-Access session plus Human Intent Signature unless a valid recovery/emergency path is active."
            ),
            rx.text(
                "POST /v1/access/lockdown freezes sessions, revokes child API keys, revokes delegated passes, preserves recovery, and creates an audit event."
            ),
            title="Lockdown action",
            variant="safety",
        ),
        responsive_grid(
            card(rx.text("Sessions frozen"), title="Affected sessions"),
            card(rx.text("Child API keys revoked"), title="Affected child keys"),
            card(rx.text("Delegated passes revoked"), title="Affected delegated passes"),
            card(rx.text("Recovery path remains"), title="Recovery-only mode"),
            card(rx.text("Audit event hash shown"), title="Tamper-evident audit"),
            card(rx.text("Offline packs invalidated when supported"), title="Optional artifacts"),
        ),
        subtitle="Support-only unlock is not available.",
    )
