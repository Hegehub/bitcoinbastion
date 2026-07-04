from __future__ import annotations

import logging

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.access.crypto.exceptions import UnsupportedSignatureSuite, UnsafeKeyMaterialError
from app.services.access.crypto.key_loading import validate_issuer_key_config
from app.services.access.crypto.signatures import Ed25519SignatureSuite, SignatureSuiteRegistry, sign_access_certificate, verify_access_certificate_signature


def _key_pair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_raw_private_key_is_never_included_in_exception_string() -> None:
    raw_private_key = "bitcoin_seed: abandon abandon abandon"

    with pytest.raises(UnsafeKeyMaterialError) as exc_info:
        Ed25519SignatureSuite().sign({"x": 1}, "access_certificate", "issuer-key-1", raw_private_key)

    assert raw_private_key not in str(exc_info.value)


def test_raw_private_key_is_never_logged(caplog: pytest.LogCaptureFixture) -> None:
    raw_private_key = "bitcoin_seed: abandon abandon abandon"
    caplog.set_level(logging.DEBUG)

    with pytest.raises(UnsafeKeyMaterialError):
        Ed25519SignatureSuite().sign({"x": 1}, "access_certificate", "issuer-key-1", raw_private_key)

    assert raw_private_key not in caplog.text


def test_raw_signature_inputs_are_not_printed(capsys: pytest.CaptureFixture[str]) -> None:
    private_key, _ = _key_pair()
    raw_payload_value = "sensitive-payload-example"

    sign_access_certificate({"safe_field": raw_payload_value}, private_key, "issuer-key-1")
    captured = capsys.readouterr()

    assert raw_payload_value not in captured.out
    assert raw_payload_value not in captured.err


def test_placeholder_keys_are_rejected() -> None:
    for placeholder in ("changeme", "secret", "test", "dev", "password", "private_key", "replace_me"):
        with pytest.raises(UnsafeKeyMaterialError):
            validate_issuer_key_config(placeholder, "issuer-key-1")


def test_unsupported_pq_signatures_are_not_silently_accepted() -> None:
    registry = SignatureSuiteRegistry()

    for alg in ("ml_dsa_65", "ml_dsa_87", "slh_dsa"):
        with pytest.raises(UnsupportedSignatureSuite):
            registry.get(alg)


def test_invalid_signature_fails_closed() -> None:
    private_key, public_key = _key_pair()
    payload = {"certificate_fingerprint": "cert_fp_example"}
    signature = sign_access_certificate(payload, private_key, "issuer-key-1")

    result = verify_access_certificate_signature(payload, public_key, ("A" if signature.signature[0] != "A" else "B") + signature.signature[1:])

    assert result.valid is False


def test_bitcoin_seed_or_wallet_private_key_material_is_not_accepted() -> None:
    for unsafe_key in ("bitcoin_seed: abandon abandon", "wallet_seed: abandon abandon", "xprv-example"):
        with pytest.raises(UnsafeKeyMaterialError):
            Ed25519SignatureSuite().sign({"x": 1}, "access_certificate", "issuer-key-1", unsafe_key)


def test_ml_kem_768_is_not_accepted_as_signature_algorithm() -> None:
    with pytest.raises(UnsupportedSignatureSuite):
        SignatureSuiteRegistry().get("ml_kem_768")
