"""Wallet auth domain constants."""

WALLET_AUTH_INTENT_TYPE = "bastion_wallet_auth_intent"
WALLET_AUTH_INTENT_VERSION = 1
REQUIRED_SIGNATURE_WARNING = (
    "This signature does not authorize a Bitcoin transaction. "
    "This signature only proves wallet control for Bastion access."
)
DEDICATED_AUTH_ADDRESS_WARNING = (
    "Use a dedicated Bastion auth wallet/address. Do not use your cold treasury wallet "
    "for routine login. Bastion will never ask for your Bitcoin seed."
)
FORBIDDEN_WALLET_SECRET_TERMS = [
    "seed",
    "private_key",
    "mnemonic",
    "xprv",
    "wallet_seed",
    "bitcoin_seed",
]
