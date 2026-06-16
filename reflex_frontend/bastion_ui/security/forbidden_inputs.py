from __future__ import annotations

SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing material",
)


def looks_like_sensitive_wallet_material(value: str) -> bool:
    """Return True for obvious wallet-secret material that must never be submitted."""

    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        return False
    if any(keyword in normalized for keyword in SENSITIVE_KEYWORDS):
        return True
    words = normalized.split()
    if len(words) in {12, 24} and all(word.isalpha() for word in words):
        return True
    return False


# Backward-compatible alias for older experimental modules that may still import it.
def contains_forbidden_material(value: str) -> bool:
    return looks_like_sensitive_wallet_material(value)
