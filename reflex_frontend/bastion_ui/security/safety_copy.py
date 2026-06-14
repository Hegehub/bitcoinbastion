REQUIRED_SAFETY_COPY: tuple[str, ...] = (
    "Advisory-only.",
    "Not legal verification.",
    "Not Bitcoin consensus proof.",
    "No custody.",
    "Public Bitcoin addresses only.",
    "Never enter seed phrases, private keys, wallet files or signing material.",
)

TRACE_SAFETY_COPY = " ".join(REQUIRED_SAFETY_COPY)

FORBIDDEN_WORDING: tuple[str, ...] = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)
