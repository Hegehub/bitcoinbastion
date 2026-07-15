"""LNURL Bech32 encoding and decoding with URL safety validation.

A valid LNURL checksum only proves encoding integrity; decoded URLs still pass
through the central URL safety policy before callers may use them.
"""
from __future__ import annotations


from app.services.lnurl.errors import (
    LNURLDecodingError,
    LNURLEncodingError,
    LNURLInputTooLargeError,
    LNURLInvalidChecksumError,
    LNURLInvalidHRPError,
    LNURLInvalidUTF8Error,
    LNURLMixedCaseError,
)
from app.services.lnurl.models import DecodedLNURL
from app.services.lnurl.redaction import fingerprint_lnurl_value
from app.services.lnurl.url_safety import MAX_LNURL_VALUE_CHARS, LNURLURLPolicy, validate_lnurl_url

LNURL_HRP = "lnurl"
BECH32_CONST = 1
BECH32M_CONST = 0x2BC830A3
_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_CHARSET_MAP = {c: i for i, c in enumerate(_CHARSET)}

def encode_lnurl(url: str, *, policy: LNURLURLPolicy | None = None) -> str:
    policy = policy or LNURLURLPolicy.remote_fetch()
    try:
        validated = validate_lnurl_url(url, policy=policy)
        raw = validated.normalized_url.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise LNURLEncodingError("URL is not valid UTF-8.") from exc
    if not raw:
        raise LNURLEncodingError("URL is required.")
    if len(raw) > policy.maximum_url_bytes:
        raise LNURLInputTooLargeError()
    data = _convertbits(raw, 8, 5, True)
    encoded = _bech32_encode(LNURL_HRP, data).lower()
    if len(encoded) > MAX_LNURL_VALUE_CHARS:
        raise LNURLInputTooLargeError()
    return encoded

def decode_lnurl(value: str, *, policy: LNURLURLPolicy | None = None) -> DecodedLNURL:
    policy = policy or LNURLURLPolicy.remote_fetch()
    if not value:
        raise LNURLDecodingError("LNURL value is required.")
    if len(value) > MAX_LNURL_VALUE_CHARS + len("lightning:"):
        raise LNURLInputTooLargeError()
    raw_value = value
    if value.lower().startswith("lightning:"):
        value = value[len("lightning:"):]
    if value.lower() != value and value.upper() != value:
        raise LNURLMixedCaseError()
    value = value.lower()
    hrp, data, variant = _bech32_decode(value)
    if hrp != LNURL_HRP:
        raise LNURLInvalidHRPError()
    if variant != "bech32":
        raise LNURLInvalidChecksumError("LNURL requires original Bech32 checksum, not Bech32m.")
    decoded = bytes(_convertbits(data, 5, 8, False))
    if b"\x00" in decoded or any(b < 32 or b == 127 for b in decoded):
        raise LNURLInvalidUTF8Error()
    try:
        url = decoded.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise LNURLInvalidUTF8Error() from exc
    if "\ufffd" in url:
        raise LNURLInvalidUTF8Error()
    validated = validate_lnurl_url(url, policy=policy)
    return DecodedLNURL(
        encoded_fingerprint=fingerprint_lnurl_value(raw_value),
        normalized_url=validated.normalized_url,
        scheme=validated.scheme,
        hostname=validated.hostname,
        port=validated.port,
        path=validated.path,
        has_query=bool(validated.query),
        is_onion=validated.is_onion,
        safety_class=validated.purpose.value,
    )

def _bech32_polymod(values: list[int]) -> int:
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i, generator in enumerate([0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]):
            if (top >> i) & 1:
                chk ^= generator
    return chk

def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def _bech32_create_checksum(hrp: str, data: list[int]) -> list[int]:
    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data + [0, 0, 0, 0, 0, 0]) ^ BECH32_CONST
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

def _bech32_encode(hrp: str, data: list[int]) -> str:
    combined = data + _bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join(_CHARSET[d] for d in combined)

def _bech32_decode(value: str) -> tuple[str, list[int], str]:
    if any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise LNURLDecodingError()
    pos = value.rfind("1")
    if pos < 1 or pos + 7 > len(value):
        raise LNURLInvalidChecksumError()
    hrp = value[:pos]
    try:
        data = [_CHARSET_MAP[c] for c in value[pos + 1:]]
    except KeyError as exc:
        raise LNURLDecodingError("LNURL contains invalid Bech32 characters.") from exc
    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    if polymod == BECH32_CONST:
        variant = "bech32"
    elif polymod == BECH32M_CONST:
        variant = "bech32m"
    else:
        raise LNURLInvalidChecksumError()
    return hrp, data[:-6], variant

def _convertbits(data: bytes | list[int], frombits: int, tobits: int, pad: bool) -> list[int]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or value >> frombits:
            raise LNURLDecodingError("Invalid bit group.")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise LNURLDecodingError("Invalid Bech32 padding.")
    return ret

# test helper to produce negative vectors without exporting a public Bech32m encoder
def _encode_bech32m_for_test(url: str) -> str:
    data = _convertbits(url.encode(), 8, 5, True)
    polymod = _bech32_polymod(_bech32_hrp_expand(LNURL_HRP) + data + [0, 0, 0, 0, 0, 0]) ^ BECH32M_CONST
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return LNURL_HRP + "1" + "".join(_CHARSET[d] for d in data + checksum)

__all__ = ["encode_lnurl", "decode_lnurl", "LNURL_HRP"]
