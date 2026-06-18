from __future__ import annotations

import re

SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "tprv",
    "wallet.dat",
    "keystore",
    "signing material",
)
EXTENDED_PRIVATE_KEY_RE = re.compile(r"\b[xyzt]prv[1-9A-HJ-NP-Za-km-z]{8,}\b")
WIF_PRIVATE_KEY_RE = re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")
JSON_KEY_MATERIAL_RE = re.compile(r'"(private_key|seed|mnemonic|xprv|yprv|zprv|tprv)"\s*:')
WORD_RE = re.compile(r"\b[a-z]{3,12}\b", re.IGNORECASE)


def _looks_like_mnemonic_phrase(value: str) -> bool:
    words = WORD_RE.findall(value)
    return len(words) in {12, 24} and len(words) == len(value.split())


def looks_like_sensitive_wallet_material(value: str) -> bool:
    """Return True for obvious wallet-secret material that must never be submitted."""

    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        return False
    if any(keyword in normalized for keyword in SENSITIVE_KEYWORDS):
        return True
    if EXTENDED_PRIVATE_KEY_RE.search(value) or WIF_PRIVATE_KEY_RE.search(value):
        return True
    if JSON_KEY_MATERIAL_RE.search(value):
        return True
    return _looks_like_mnemonic_phrase(normalized)


# Backward-compatible alias for older experimental modules that may still import it.
def contains_forbidden_material(value: str) -> bool:
    return looks_like_sensitive_wallet_material(value)
