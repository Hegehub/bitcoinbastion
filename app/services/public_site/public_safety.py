def safety_principles() -> list[str]:
    return [
        "Bitcoin-first",
        "No-custody",
        "Watch-only",
        "Advisory-only",
        "Evidence-based",
        "Operator-controlled",
        "No seed/private key handling",
        "No transaction signing",
        "No transaction broadcasting",
        "No legal verdict",
        "No consensus proof",
    ]


def public_warnings() -> list[str]:
    return [
        "This endpoint is advisory-only.",
        "This endpoint does not provide legal verification.",
        "Bitcoin Bastion does not accept seed phrases or private keys.",
        "This endpoint does not authorize or sign transactions.",
    ]
