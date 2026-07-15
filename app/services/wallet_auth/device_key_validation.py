"""Device public-key validation for wallet-auth device binding."""

from __future__ import annotations

import base64
import binascii
import hmac
import re
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.services.access.crypto.hashing import sha256_prefixed
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input

_SUPPORTED_ALGORITHMS = frozenset({"ed25519"})
_PRIVATE_MARKERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
)
_MNEMONIC_WORDS_RE = re.compile(r"\b(abandon|ability|able|about|above|absent|absorb|abstract)\b", re.I)


class DeviceKeyInvalidError(ValueError):
    """Safe device-key validation error that never includes key material."""


class DeviceKeyFingerprintMismatchError(DeviceKeyInvalidError):
    """Raised when a client-supplied fingerprint does not match recomputation."""


@dataclass(frozen=True, slots=True)
class NormalizedDevicePublicKey:
    algorithm: str
    public_key_bytes: bytes
    public_key_b64: str
    fingerprint: str

    def safe_summary(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "device_key_fingerprint": self.fingerprint}


def detect_forbidden_private_material(value: str | bytes) -> None:
    text = _decode_for_detection(value)
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in _PRIVATE_MARKERS):
        raise DeviceKeyInvalidError("device_key_private_material_not_allowed")
    if lowered.startswith(("xprv", "yprv", "zprv", "tprv")):
        raise DeviceKeyInvalidError("device_key_extended_private_key_not_allowed")
    if _MNEMONIC_WORDS_RE.search(text) and len(text.split()) >= 8:
        raise DeviceKeyInvalidError("device_key_mnemonic_not_allowed")
    if isinstance(value, bytes) and len(value) >= 48 and value[:1] == b"\x30":
        raise DeviceKeyInvalidError("device_key_private_der_not_allowed")
    try:
        reject_forbidden_wallet_secret_input(text, "device_public_key")
    except ValueError as exc:
        raise DeviceKeyInvalidError("device_key_forbidden_secret_material") from exc


def validate_key_algorithm(algorithm: str) -> str:
    normalized = algorithm.strip().lower().replace("_", "-")
    if normalized == "ed25519":
        return "ed25519"
    raise DeviceKeyInvalidError("device_key_unsupported_algorithm")


def normalize_device_public_key(public_key: str | bytes, *, algorithm: str = "ed25519") -> NormalizedDevicePublicKey:
    normalized_algorithm = validate_key_algorithm(algorithm)
    detect_forbidden_private_material(public_key)
    key_bytes = _extract_public_key_bytes(public_key, normalized_algorithm)
    fingerprint = compute_device_key_fingerprint(key_bytes, algorithm=normalized_algorithm)
    return NormalizedDevicePublicKey(
        algorithm=normalized_algorithm,
        public_key_bytes=key_bytes,
        public_key_b64=base64.b64encode(key_bytes).decode("ascii"),
        fingerprint=fingerprint,
    )


def validate_device_public_key(
    public_key: str | bytes,
    *,
    algorithm: str = "ed25519",
    expected_fingerprint: str | None = None,
) -> NormalizedDevicePublicKey:
    normalized = normalize_device_public_key(public_key, algorithm=algorithm)
    if expected_fingerprint is not None and not constant_time_fingerprint_equal(
        normalized.fingerprint, expected_fingerprint
    ):
        raise DeviceKeyFingerprintMismatchError("device_key_fingerprint_mismatch")
    return normalized


def compute_device_key_fingerprint(public_key: bytes | str, *, algorithm: str = "ed25519") -> str:
    normalized_algorithm = validate_key_algorithm(algorithm)
    key_bytes = _extract_public_key_bytes(public_key, normalized_algorithm)
    payload = b"bastion-device-public-key-v1\x00" + normalized_algorithm.encode("ascii") + b"\x00" + key_bytes
    return sha256_prefixed(payload)


def constant_time_fingerprint_equal(first: str, second: str) -> bool:
    return hmac.compare_digest(first.encode("utf-8"), second.encode("utf-8"))


def validate_attestation_metadata(metadata: dict[str, object] | None) -> dict[str, object]:
    if not metadata:
        return {}
    clean: dict[str, object] = {}
    for key, value in metadata.items():
        key_text = str(key).lower()
        if key_text in {"private_key", "seed", "mnemonic", "xprv", "serial_number", "signature"}:
            raise DeviceKeyInvalidError("device_attestation_forbidden_field")
        if isinstance(value, str):
            detect_forbidden_private_material(value)
        clean[str(key)] = value
    return clean


def _extract_public_key_bytes(public_key: str | bytes, algorithm: str) -> bytes:
    if algorithm != "ed25519":
        raise DeviceKeyInvalidError("device_key_unsupported_algorithm")
    if isinstance(public_key, str) and "BEGIN PUBLIC KEY" in public_key:
        loaded = serialization.load_pem_public_key(public_key.encode("utf-8"))
        if not isinstance(loaded, Ed25519PublicKey):
            raise DeviceKeyInvalidError("device_key_wrong_algorithm")
        return loaded.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    key_bytes = _decode_public_key_bytes(public_key)
    if len(key_bytes) != 32:
        raise DeviceKeyInvalidError("device_key_malformed_public_key")
    try:
        Ed25519PublicKey.from_public_bytes(key_bytes)
    except ValueError as exc:
        raise DeviceKeyInvalidError("device_key_malformed_public_key") from exc
    return key_bytes


def _decode_public_key_bytes(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    text = value.strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", text):
        return bytes.fromhex(text)
    try:
        return base64.b64decode(text, validate=True)
    except binascii.Error as exc:
        raise DeviceKeyInvalidError("device_key_malformed_public_key") from exc


def _decode_for_detection(value: str | bytes) -> str:
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="ignore")
