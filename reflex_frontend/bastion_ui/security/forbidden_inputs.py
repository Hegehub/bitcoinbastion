FORBIDDEN_PATTERNS: list[str] = [
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "12 words",
    "24 words",
    "signing material",
]

FORBIDDEN_INPUT_PATTERNS: tuple[str, ...] = tuple(FORBIDDEN_PATTERNS)


def contains_forbidden_material(value: str) -> bool:
    normalized = value.lower()
    return any(pattern in normalized for pattern in FORBIDDEN_PATTERNS)
