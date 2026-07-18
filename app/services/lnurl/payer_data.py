"""Strict LNURL-pay payerData parsing and declaration helpers.

payerData is wallet-supplied metadata.  The only field Bastion accepts in this
prompt is ``auth``; personal fields remain disabled by default and the parsed
payload is never treated as settlement, a PoP session, or authorization.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.services.access.crypto.hashing import hash_canonical_json_prefixed, sha256_prefixed

MAX_PAYERDATA_BYTES = 4096
K1_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
COMPRESSED_SECP256K1_RE = re.compile(r"^(02|03)[0-9a-f]{64}$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
MAX_DER_SIGNATURE_BYTES = 80
MIN_DER_SIGNATURE_BYTES = 8


class LNURLPayerDataMode(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DISABLED = "disabled"


class LNURLPayerDataError(ValueError):
    def __init__(self, reason_code: str, public_reason: str = "Payer authentication failed.") -> None:
        self.reason_code = reason_code
        self.public_reason = public_reason
        super().__init__(reason_code)


class PayerDataMissingError(LNURLPayerDataError): ...
class PayerDataTooLargeError(LNURLPayerDataError): ...
class PayerDataInvalidJSONError(LNURLPayerDataError): ...
class PayerDataAuthMissingError(LNURLPayerDataError): ...
class PayerDataAuthInvalidError(LNURLPayerDataError): ...


@dataclass(frozen=True, slots=True)
class ParsedPayerAuth:
    key: str
    k1: str
    sig: str
    key_fingerprint: str
    proof_hash: str


@dataclass(frozen=True, slots=True)
class ParsedPayerData:
    present: bool
    auth: ParsedPayerAuth | None
    payload_hash: str | None
    input_trust: str = "untrusted_external_metadata"


def build_payer_data_declaration(*, k1: str, mandatory: bool) -> dict[str, Any]:
    """Return the LNURL-pay ``payerData`` declaration without internal IDs."""

    _validate_k1(k1.lower())
    return {"auth": {"mandatory": bool(mandatory), "k1": k1.lower()}}


def parse_payerdata(raw_payerdata: str | bytes | bytearray | dict[str, Any] | None, *, max_bytes: int = MAX_PAYERDATA_BYTES, require_auth: bool = False) -> ParsedPayerData:
    if raw_payerdata is None:
        if require_auth:
            raise PayerDataMissingError("payerdata_missing")
        return ParsedPayerData(present=False, auth=None, payload_hash=None)
    if isinstance(raw_payerdata, dict):
        payload = raw_payerdata
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    else:
        encoded = bytes(raw_payerdata) if isinstance(raw_payerdata, (bytes, bytearray)) else str(raw_payerdata).encode("utf-8")
        if len(encoded) > max_bytes:
            raise PayerDataTooLargeError("payerdata_too_large")
        try:
            text = encoded.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PayerDataInvalidJSONError("payerdata_invalid_json") from exc
        try:
            payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PayerDataInvalidJSONError("payerdata_invalid_json") from exc
    if len(encoded) > max_bytes:
        raise PayerDataTooLargeError("payerdata_too_large")
    if not isinstance(payload, dict):
        raise PayerDataInvalidJSONError("payerdata_invalid_json")
    extra = set(payload) - {"auth"}
    if extra:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")
    auth_payload = payload.get("auth")
    if auth_payload is None:
        if require_auth:
            raise PayerDataAuthMissingError("payerdata_auth_missing")
        return ParsedPayerData(present=True, auth=None, payload_hash=hash_canonical_json_prefixed(payload))
    auth = _parse_auth(auth_payload)
    return ParsedPayerData(present=True, auth=auth, payload_hash=hash_canonical_json_prefixed({"auth": {"key_fingerprint": auth.key_fingerprint, "k1_hash": sha256_prefixed(auth.k1), "proof_hash": auth.proof_hash}}))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_json_key")
        out[key] = value
    return out


def _parse_auth(auth_payload: Any) -> ParsedPayerAuth:
    if not isinstance(auth_payload, dict):
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")
    if set(auth_payload) != {"key", "k1", "sig"}:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")
    key = _normalize_hex(auth_payload["key"], reason="payerdata_auth_invalid")
    k1 = _normalize_hex(auth_payload["k1"], reason="payerdata_auth_invalid")
    sig = _normalize_hex(auth_payload["sig"], reason="payerdata_auth_invalid")
    if COMPRESSED_SECP256K1_RE.fullmatch(key) is None:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")
    _validate_k1(k1)
    _validate_der_signature(sig)
    key_fingerprint = sha256_prefixed(bytes.fromhex(key))
    proof_hash = hash_canonical_json_prefixed({"key_fingerprint": key_fingerprint, "k1_hash": sha256_prefixed(k1), "sig_hash": sha256_prefixed(sig)})
    return ParsedPayerAuth(key=key, k1=k1, sig=sig, key_fingerprint=key_fingerprint, proof_hash=proof_hash)


def _normalize_hex(value: Any, *, reason: str) -> str:
    if not isinstance(value, str):
        raise PayerDataAuthInvalidError(reason)
    if value.startswith(("0x", "0X")) or any(ch.isspace() for ch in value):
        raise PayerDataAuthInvalidError(reason)
    normalized = value.lower()
    if HEX_RE.fullmatch(normalized) is None or len(normalized) % 2:
        raise PayerDataAuthInvalidError(reason)
    return normalized


def _validate_k1(k1: str) -> None:
    if K1_HEX_RE.fullmatch(k1) is None:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")


def _validate_der_signature(sig: str) -> None:
    try:
        sig_bytes = bytes.fromhex(sig)
    except ValueError as exc:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid") from exc
    if not (MIN_DER_SIGNATURE_BYTES <= len(sig_bytes) <= MAX_DER_SIGNATURE_BYTES):
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")
    if sig_bytes[0] != 0x30 or len(sig_bytes) < 2 or sig_bytes[1] != len(sig_bytes) - 2:
        raise PayerDataAuthInvalidError("payerdata_auth_invalid")


__all__ = [
    "LNURLPayerDataMode",
    "LNURLPayerDataError",
    "PayerDataMissingError",
    "PayerDataTooLargeError",
    "PayerDataInvalidJSONError",
    "PayerDataAuthMissingError",
    "PayerDataAuthInvalidError",
    "ParsedPayerAuth",
    "ParsedPayerData",
    "build_payer_data_declaration",
    "parse_payerdata",
]
