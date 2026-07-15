"""LNURL domain constants and safety warnings."""

from app.domain.lnurl.auth import LNURLAuthAction

LNURL_K1_BYTES = 32
LNURL_AUTH_DEFAULT_TTL_SECONDS = 300
LNURL_AUTH_MAX_TTL_SECONDS = 600
LNURL_PAY_DEFAULT_TTL_SECONDS = 900
LNURL_PAY_MAX_TTL_SECONDS = 3600
LNURL_WITHDRAW_DEFAULT_TTL_SECONDS = 300
LNURL_WITHDRAW_MAX_TTL_SECONDS = 900
LNURL_AUTH_ALLOWED_ACTIONS = frozenset(LNURLAuthAction)
LNURL_AUTH_STABLE_DOMAIN_WARNING = (
    "LNURL-auth identity is domain-specific. Changing the authentication domain requires an explicit principal migration and linking process."
)
LNURL_AUTH_CONTROL_WARNING = (
    "LNURL-auth proves control of a domain-specific Lightning wallet key. It does not prove ownership of an on-chain Bitcoin treasury address."
)
LNURL_PAYMENT_SETTLEMENT_WARNING = "Invoice creation does not prove payment. Bastion must verify settlement before issuing an entitlement."
LNURL_WITHDRAW_SECURITY_WARNING = (
    "LNURL-withdraw transfers value to the holder of a valid withdrawal challenge. Authentication and Policy Engine approval are required before issuing valuable withdrawal requests."
)
LNURL_PAYERDATA_PRIVACY_WARNING = "payerData must be minimized. Bastion does not require email or legal identity for wallet-first access by default."
LIGHTNING_ADDRESS_IDENTITY_WARNING = "A Lightning Address is a payment-routing identifier, not a Bastion identity or authorization factor."
LNURL_COMMENT_SECURITY_WARNING = "LNURL payment comments are untrusted metadata and must never authorize access, recovery, roles, or entitlements."
LNURL_FORBIDDEN_SECRET_FIELDS = frozenset(
    {
        "seed",
        "mnemonic",
        "private_key",
        "wallet_seed",
        "bitcoin_seed",
        "xprv",
        "linking_private_key",
        "session_private_key",
        "issuer_private_key",
    }
)
# Backward-compatible aliases used by earlier schemas/tests.
LNURL_WITHDRAW_AUTH_REQUIRED_WARNING = LNURL_WITHDRAW_SECURITY_WARNING
LNURL_INVOICE_NOT_SETTLED_WARNING = LNURL_PAYMENT_SETTLEMENT_WARNING
LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING = LIGHTNING_ADDRESS_IDENTITY_WARNING
