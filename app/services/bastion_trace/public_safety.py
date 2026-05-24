FORBIDDEN_TERMS = {"clean", "dirty", "criminal", "guaranteed", "approved", "safe"}


def default_warnings() -> list[str]:
    return [
        "Never enter seed phrases, private keys or wallet files.",
        "Bitcoin Bastion only checks public Bitcoin addresses.",
        "This report is advisory only and not a legal verdict.",
        "This report is not a Bitcoin consensus proof.",
    ]
