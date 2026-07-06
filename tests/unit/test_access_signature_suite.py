from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.access.crypto.exceptions import (
    InvalidPublicKey,
    MissingIssuerKey,
    UnsupportedSignatureSuite,
    UnsafeKeyMaterialError,
)
from app.services.access.crypto.key_loading import load_issuer_private_key_from_env, validate_issuer_key_config
from app.services.access.crypto.signatures import (
    Ed25519SignatureSuite,
    PQ_SIGNATURE_SUITES_KNOWN,
    SignatureSuiteRegistry,
    build_signing_message,
    sign_access_certificate,
    verify_access_certificate_signature,
)


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


def test_ed25519_sign_verify_succeeds_for_access_certificate_context() -> None:
    private_key, public_key = _key_pair()
    payload = {"certificate_fingerprint": "cert_fp_example", "plan_code": "pro_pass"}

    issuer_signature = sign_access_certificate(payload, private_key, "issuer-key-1")
    result = verify_access_certificate_signature(payload, public_key, issuer_signature.signature)

    assert issuer_signature.alg == "ed25519"
    assert issuer_signature.key_id == "issuer-key-1"
    assert result.valid is True
    assert result.public_key_fingerprint == issuer_signature.public_key_fingerprint


def test_tampered_payload_fails_verification() -> None:
    private_key, public_key = _key_pair()
    signature = sign_access_certificate({"plan_code": "pro_pass"}, private_key, "issuer-key-1")

    result = verify_access_certificate_signature({"plan_code": "enterprise_pass"}, public_key, signature.signature)

    assert result.valid is False


def test_tampered_signature_fails_verification() -> None:
    private_key, public_key = _key_pair()
    signature = sign_access_certificate({"plan_code": "pro_pass"}, private_key, "issuer-key-1")
    tampered = signature.signature[:-1] + ("A" if signature.signature[-1] != "A" else "B")

    result = verify_access_certificate_signature({"plan_code": "pro_pass"}, public_key, tampered)

    assert result.valid is False


def test_same_payload_under_different_contexts_produces_different_signatures() -> None:
    private_key, _ = _key_pair()
    suite = Ed25519SignatureSuite()
    payload = {"id": "object_example"}

    certificate_signature = suite.sign(payload, "access_certificate", "issuer-key-1", private_key)
    entitlement_signature = suite.sign(payload, "subscription_entitlement", "issuer-key-1", private_key)

    assert certificate_signature.signature != entitlement_signature.signature
    assert build_signing_message("access_certificate", payload) != build_signing_message("subscription_entitlement", payload)


def test_canonical_json_ordering_is_stable_for_signatures() -> None:
    private_key, public_key = _key_pair()
    signature = sign_access_certificate({"b": 2, "a": 1}, private_key, "issuer-key-1")

    assert verify_access_certificate_signature({"a": 1, "b": 2}, public_key, signature.signature).valid is True


def test_public_key_fingerprint_returns_sha256_prefix() -> None:
    _, public_key = _key_pair()

    fingerprint = Ed25519SignatureSuite().public_key_fingerprint(public_key)

    assert fingerprint.startswith("sha256:")


def test_unsupported_ml_dsa_suite_fails_closed() -> None:
    registry = SignatureSuiteRegistry()

    assert "ml_dsa_65" in registry.unsupported_algorithms()
    with pytest.raises(UnsupportedSignatureSuite):
        registry.get("ml_dsa_65")


def test_unsupported_slh_dsa_suite_fails_closed() -> None:
    registry = SignatureSuiteRegistry()

    assert "slh_dsa" in registry.unsupported_algorithms()
    with pytest.raises(UnsupportedSignatureSuite):
        registry.get("slh_dsa")


def test_ml_kem_cannot_be_used_as_signature_suite() -> None:
    registry = SignatureSuiteRegistry()

    assert "ml_kem_768" not in registry.supported_algorithms()
    assert "ml_kem_768" not in registry.unsupported_algorithms()
    with pytest.raises(UnsupportedSignatureSuite):
        registry.get("ml_kem_768")


def test_missing_issuer_key_raises_missing_issuer_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_ISSUER_PRIVATE_KEY", raising=False)

    with pytest.raises(MissingIssuerKey):
        load_issuer_private_key_from_env()


def test_placeholder_issuer_key_raises_unsafe_key_material() -> None:
    with pytest.raises(UnsafeKeyMaterialError):
        validate_issuer_key_config("changeme", "issuer-key-1")


def test_invalid_public_key_returns_invalid_result_and_direct_fingerprint_raises() -> None:
    private_key, _ = _key_pair()
    signature = sign_access_certificate({"plan_code": "pro_pass"}, private_key, "issuer-key-1")
    invalid_public_key = base64.urlsafe_b64encode(b"not-a-valid-ed25519-public-key").decode("ascii")

    result = verify_access_certificate_signature({"plan_code": "pro_pass"}, invalid_public_key, signature.signature)

    assert result.valid is False
    with pytest.raises(InvalidPublicKey):
        Ed25519SignatureSuite().public_key_fingerprint(invalid_public_key)


def test_known_future_pq_signature_metadata_is_registered_but_unsupported() -> None:
    assert PQ_SIGNATURE_SUITES_KNOWN == ["ml_dsa_65", "ml_dsa_87", "slh_dsa"]
