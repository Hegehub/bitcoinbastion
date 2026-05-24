REDACT_KEYS = {'authorization', 'cookie', 'x-api-key', 'seed', 'mnemonic', 'private_key', 'xprv', 'wif'}


def sanitize_mapping(data: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in data.items():
        if k.lower() in REDACT_KEYS:
            out[k] = 'redacted'
        else:
            out[k] = v[:128]
    return out
