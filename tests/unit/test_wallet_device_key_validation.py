from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.wallet_auth.device_key_validation import (
    DeviceKeyFingerprintMismatchError,
    DeviceKeyInvalidError,
    compute_device_key_fingerprint,
    constant_time_fingerprint_equal,
    detect_forbidden_private_material,
    normalize_device_public_key,
    validate_device_public_key,
)


def _public_key_bytes() -> bytes:
    return Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def test_valid_ed25519_public_key_accepted() -> None:
    normalized = validate_device_public_key(_public_key_bytes(), algorithm="ed25519")
    assert normalized.algorithm == "ed25519"
    assert normalized.fingerprint.startswith("sha256:")


def test_normalized_key_produces_stable_fingerprint() -> None:
    key = _public_key_bytes()
    b64 = base64.b64encode(key).decode("ascii")
    first = normalize_device_public_key(key)
    second = normalize_device_public_key(b64)
    assert first.public_key_b64 == second.public_key_b64
    assert first.fingerprint == second.fingerprint
    assert compute_device_key_fingerprint(key) == first.fingerprint


def test_malformed_public_key_rejected() -> None:
    with pytest.raises(DeviceKeyInvalidError, match="device_key_malformed_public_key"):
        validate_device_public_key("not-base64")


def test_unsupported_algorithm_rejected() -> None:
    with pytest.raises(DeviceKeyInvalidError, match="device_key_unsupported_algorithm"):
        validate_device_public_key(_public_key_bytes(), algorithm="rsa")


def test_private_pem_rejected() -> None:
    private_pem = Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    with pytest.raises(DeviceKeyInvalidError, match="private_material"):
        validate_device_public_key(private_pem)


def test_private_der_like_material_rejected() -> None:
    private_der = Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with pytest.raises(DeviceKeyInvalidError, match="private_der"):
        detect_forbidden_private_material(private_der)


def test_mnemonic_like_input_rejected() -> None:
    mnemonic = "abandon ability able about above absent absorb abstract abandon ability able about"
    with pytest.raises(DeviceKeyInvalidError, match="mnemonic"):
        validate_device_public_key(mnemonic)


def test_xprv_rejected() -> None:
    with pytest.raises(DeviceKeyInvalidError, match="extended_private_key"):
        validate_device_public_key("xprv9s21ZrQH143Kprivate")


def test_client_provided_mismatched_fingerprint_rejected() -> None:
    with pytest.raises(DeviceKeyFingerprintMismatchError):
        validate_device_public_key(_public_key_bytes(), expected_fingerprint="sha256:" + "00" * 32)


def test_constant_time_comparison_helper() -> None:
    fingerprint = validate_device_public_key(_public_key_bytes()).fingerprint
    assert constant_time_fingerprint_equal(fingerprint, fingerprint)
    assert not constant_time_fingerprint_equal(fingerprint, "sha256:" + "11" * 32)


def test_sensitive_input_not_in_error_message() -> None:
    secret = "xprv9s21ZrQH143Ksecretmaterial"
    with pytest.raises(DeviceKeyInvalidError) as exc:
        validate_device_public_key(secret)
    assert secret not in str(exc.value)
