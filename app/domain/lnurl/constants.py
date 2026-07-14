"""LNURL domain constants."""

LNURL_K1_BYTES = 32
LNURL_AUTH_DEFAULT_TTL_SECONDS = 300
LNURL_PAY_DEFAULT_TTL_SECONDS = 900
LNURL_WITHDRAW_DEFAULT_TTL_SECONDS = 300
LNURL_AUTH_STABLE_DOMAIN_WARNING = (
    "LNURL-auth domain must be stable. Changing the auth domain can create a different "
    "wallet-derived principal."
)
LNURL_WITHDRAW_AUTH_REQUIRED_WARNING = (
    "Valuable LNURL-withdraw requests require authentication and policy approval before QR issuance."
)
LNURL_PAYERDATA_PRIVACY_WARNING = "payerData must be minimal. Do not request email or name by default."
LNURL_INVOICE_NOT_SETTLED_WARNING = "Invoice issued does not mean payment settled."
LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING = "Lightning Address is payment routing UX, not identity by itself."
