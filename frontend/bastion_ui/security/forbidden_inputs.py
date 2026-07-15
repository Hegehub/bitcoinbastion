from __future__ import annotations

import re

SENSITIVE_WALLET_INPUT_MESSAGE = (
    "This looks like sensitive wallet material. Bitcoin Bastion Trace only accepts public "
    "Bitcoin addresses. Never enter seed phrases, private keys, wallet files, or signing material."
)

SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "seed phrase",
    "mnemonic",
    "mnemonic phrase",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "tprv",
    "wallet.dat",
    "keystore",
    "signing material",
)
WORD_RE = re.compile(r"\b[a-z]{3,12}\b", re.IGNORECASE)
WIF_RE = re.compile(r"^[5KL][1-9A-HJ-NP-Za-km-z]{50,51}$")
JSON_KEY_RE = re.compile(r'"(private|seed|mnemonic|xprv|yprv|zprv|tprv|keystore)"', re.I)


def looks_like_sensitive_wallet_material(value: str) -> bool:
    """Return True for wallet-secret-like material that must never be submitted."""

    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        return False
    if any(keyword in normalized for keyword in SENSITIVE_KEYWORDS):
        return True
    if WIF_RE.match(value.strip()):
        return True
    if JSON_KEY_RE.search(value):
        return True
    words = WORD_RE.findall(normalized)
    if len(words) in {12, 24} and len(words) == len(normalized.split()):
        return True
    return False


# Backward-compatible alias for older experimental modules that may still import it.
def contains_forbidden_material(value: str) -> bool:
    return looks_like_sensitive_wallet_material(value)
