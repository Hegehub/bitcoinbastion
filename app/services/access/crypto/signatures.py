"""Signature-suite abstraction for Bastion Proof-of-Access Auth.

Ed25519 is the supported classical MVP signature suite. ML-DSA and SLH-DSA are
registered as future signature suites but fail closed until real audited
implementations and tests are integrated. ML-KEM is documented as a future KEM
for session-envelope/key-establishment work and is never exposed as a signing
algorithm by this module.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature as CryptographyInvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.services.access.crypto.exceptions import (
    InvalidIssuerKey,
    InvalidPublicKey,
    UnsupportedSignatureSuite,
    UnsafeKeyMaterialError,
)
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.access.crypto.key_loading import validate_issuer_key_config, validate_key_material_is_not_placeholder


class SignatureAlgorithm(StrEnum):
    ED25519 = "ed25519"
    ML_DSA_65 = "ml_dsa_65"
    ML_DSA_87 = "ml_dsa_87"
    SLH_DSA = "slh_dsa"


PQ_SIGNATURE_SUITES_KNOWN = [
    "ml_dsa_65",  # Future Access Certificate / Subscription Entitlement signature support.
    "ml_dsa_87",  # Future higher-security Access signature support.
    "slh_dsa",  # Future backup/root/long-term trust signature support.
]
PQ_KEM_SUITES_KNOWN = [
    "ml_kem_768",  # Future KEM/session-envelope support, not a signature suite.
]
SUPPORTED_SIGNATURE_ALGORITHMS = [SignatureAlgorithm.ED25519.value]
SUPPORTED_SIGNING_CONTEXTS = frozenset(
    {
        "access_certificate",
        "subscription_entitlement",
        "access_challenge",
        "access_session",
        "human_intent",
        "delegated_pass",
        "revocation_epoch",
        "audit_checkpoint",
        "offline_validity_pack",
        "lnurl_payment_proof",
        "lnurl_receipt_packet",
        "recovery_factor_receipt",
    }
)


@dataclass(frozen=True, slots=True)
class IssuerSignature:
    alg: str
    key_id: str
    crypto_epoch: int
    signature: str
    public_key_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class SignatureVerificationResult:
    valid: bool
    alg: str
    key_id: str | None = None
    public_key_fingerprint: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SigningInput:
    payload: dict[str, Any] | str | bytes
    context: str
    crypto_epoch: int = 1


class SignatureSuite(Protocol):
    alg: str

    def sign(
        self,
        payload: dict[str, Any] | str | bytes,
        context: str,
        key_id: str,
        private_key: str | bytes,
        crypto_epoch: int = 1,
    ) -> IssuerSignature: ...

    def verify(
        self,
        payload: dict[str, Any] | str | bytes,
        context: str,
        public_key: str | bytes,
        signature: str,
    ) -> SignatureVerificationResult: ...

    def public_key_fingerprint(self, public_key: str | bytes) -> str: ...


def build_signing_message(context: str, payload: dict[str, Any] | str | bytes) -> bytes:
    """Build a domain-separated signing message for the supported context."""

    if context not in SUPPORTED_SIGNING_CONTEXTS:
        raise ValueError("Unsupported signing context")
    if isinstance(payload, Mapping):
        canonical_payload = canonical_json(payload)
    elif isinstance(payload, bytes):
        canonical_payload = payload.decode("utf-8", errors="surrogateescape")
    elif isinstance(payload, str):
        canonical_payload = payload
    else:
        raise TypeError("payload must be a dict, str, or bytes")
    return f"BastionProofOfAccess:v1:{context}\n{canonical_payload}".encode("utf-8", errors="surrogateescape")


class Ed25519SignatureSuite:
    alg = SignatureAlgorithm.ED25519.value

    def sign(
        self,
        payload: dict[str, Any] | str | bytes,
        context: str,
        key_id: str,
        private_key: str | bytes,
        crypto_epoch: int = 1,
    ) -> IssuerSignature:
        validate_issuer_key_config(_key_material_to_str(private_key), key_id)
        signing_key = _load_ed25519_private_key(private_key)
        public_key = signing_key.public_key()
        message = build_signing_message(context, payload)
        signature = _base64url_encode(signing_key.sign(message))
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return IssuerSignature(
            alg=self.alg,
            key_id=key_id,
            crypto_epoch=crypto_epoch,
            signature=signature,
            public_key_fingerprint=sha256_prefixed(public_bytes),
        )

    def verify(
        self,
        payload: dict[str, Any] | str | bytes,
        context: str,
        public_key: str | bytes,
        signature: str,
    ) -> SignatureVerificationResult:
        try:
            verify_key = _load_ed25519_public_key(public_key)
            signature_bytes = _base64url_decode(signature)
            verify_key.verify(signature_bytes, build_signing_message(context, payload))
            return SignatureVerificationResult(
                valid=True,
                alg=self.alg,
                public_key_fingerprint=self.public_key_fingerprint(public_key),
            )
        except InvalidPublicKey as exc:
            return SignatureVerificationResult(valid=False, alg=self.alg, reason=str(exc))
        except (CryptographyInvalidSignature, ValueError, TypeError):
            return SignatureVerificationResult(valid=False, alg=self.alg, reason="Invalid signature")

    def public_key_fingerprint(self, public_key: str | bytes) -> str:
        verify_key = _load_ed25519_public_key(public_key)
        public_bytes = verify_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return sha256_prefixed(public_bytes)


class _UnsupportedSignatureSuite:
    def __init__(self, alg: str) -> None:
        self.alg = alg

    def sign(self, *_args: object, **_kwargs: object) -> IssuerSignature:
        raise UnsupportedSignatureSuite(f"Signature suite is not supported: {self.alg}")

    def verify(self, *_args: object, **_kwargs: object) -> SignatureVerificationResult:
        raise UnsupportedSignatureSuite(f"Signature suite is not supported: {self.alg}")

    def public_key_fingerprint(self, *_args: object, **_kwargs: object) -> str:
        raise UnsupportedSignatureSuite(f"Signature suite is not supported: {self.alg}")


class SignatureSuiteRegistry:
    def __init__(self) -> None:
        self._supported: dict[str, SignatureSuite] = {SignatureAlgorithm.ED25519.value: Ed25519SignatureSuite()}
        self._unsupported = set(PQ_SIGNATURE_SUITES_KNOWN)

    def get(self, alg: str) -> SignatureSuite:
        normalized = alg.strip().lower()
        if normalized in self._supported:
            return self._supported[normalized]
        if normalized in self._unsupported or normalized in PQ_KEM_SUITES_KNOWN:
            raise UnsupportedSignatureSuite(f"Signature suite is not supported: {normalized}")
        raise UnsupportedSignatureSuite(f"Unknown signature suite: {normalized}")

    def is_supported(self, alg: str) -> bool:
        return alg.strip().lower() in self._supported

    def supported_algorithms(self) -> list[str]:
        return sorted(self._supported)

    def unsupported_algorithms(self) -> list[str]:
        return sorted(self._unsupported)


def sign_access_certificate(payload: dict[str, Any], private_key: str, key_id: str, crypto_epoch: int = 1) -> IssuerSignature:
    return Ed25519SignatureSuite().sign(payload, "access_certificate", key_id, private_key, crypto_epoch)


def verify_access_certificate_signature(payload: dict[str, Any], public_key: str, signature: str) -> SignatureVerificationResult:
    return Ed25519SignatureSuite().verify(payload, "access_certificate", public_key, signature)


def sign_subscription_entitlement(payload: dict[str, Any], private_key: str, key_id: str, crypto_epoch: int = 1) -> IssuerSignature:
    return Ed25519SignatureSuite().sign(payload, "subscription_entitlement", key_id, private_key, crypto_epoch)


def verify_subscription_entitlement_signature(payload: dict[str, Any], public_key: str, signature: str) -> SignatureVerificationResult:
    return Ed25519SignatureSuite().verify(payload, "subscription_entitlement", public_key, signature)



def sign_lnurl_payment_proof(payload: dict[str, Any], private_key: str, key_id: str, crypto_epoch: int = 1) -> IssuerSignature:
    return Ed25519SignatureSuite().sign(payload, "lnurl_payment_proof", key_id, private_key, crypto_epoch)


def verify_lnurl_payment_proof_signature(payload: dict[str, Any], public_key: str, signature: str) -> SignatureVerificationResult:
    return Ed25519SignatureSuite().verify(payload, "lnurl_payment_proof", public_key, signature)

def verify_device_challenge_signature(challenge_payload: dict[str, Any], device_public_key: str, signature: str) -> SignatureVerificationResult:
    return Ed25519SignatureSuite().verify(challenge_payload, "access_challenge", device_public_key, signature)


def _key_material_to_str(key_material: str | bytes) -> str:
    if isinstance(key_material, bytes):
        return key_material.decode("utf-8", errors="ignore")
    return key_material


def _load_ed25519_private_key(private_key: str | bytes) -> Ed25519PrivateKey:
    try:
        validate_key_material_is_not_placeholder(private_key)
        key_bytes = _decode_key_material(private_key)
        if _looks_like_pem(private_key):
            loaded = serialization.load_pem_private_key(key_bytes, password=None)
            if not isinstance(loaded, Ed25519PrivateKey):
                raise InvalidIssuerKey("Issuer key must be an Ed25519 private key")
            return loaded
        if len(key_bytes) != 32:
            raise InvalidIssuerKey("Issuer key must be Ed25519 PEM or 32-byte raw base64")
        return Ed25519PrivateKey.from_private_bytes(key_bytes)
    except UnsafeKeyMaterialError:
        raise
    except InvalidIssuerKey:
        raise
    except Exception as exc:
        raise InvalidIssuerKey("Issuer private key could not be loaded") from exc


def _load_ed25519_public_key(public_key: str | bytes) -> Ed25519PublicKey:
    try:
        key_bytes = _decode_key_material(public_key)
        if _looks_like_pem(public_key):
            loaded = serialization.load_pem_public_key(key_bytes)
            if not isinstance(loaded, Ed25519PublicKey):
                raise InvalidPublicKey("Public key must be an Ed25519 public key")
            return loaded
        if len(key_bytes) != 32:
            raise InvalidPublicKey("Public key must be Ed25519 PEM or 32-byte raw base64")
        return Ed25519PublicKey.from_public_bytes(key_bytes)
    except InvalidPublicKey:
        raise
    except Exception as exc:
        raise InvalidPublicKey("Public key could not be loaded") from exc


def _decode_key_material(key_material: str | bytes) -> bytes:
    if isinstance(key_material, bytes):
        if key_material.startswith(b"-----BEGIN"):
            return key_material
        return _decode_base64_raw(key_material)
    stripped = key_material.strip()
    if stripped.startswith("-----BEGIN"):
        return stripped.encode("utf-8")
    return _decode_base64_raw(stripped.encode("ascii"))


def _decode_base64_raw(value: bytes) -> bytes:
    padded = value + b"=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded)
    except Exception as exc:
        raise ValueError("Invalid base64 key material") from exc


def _looks_like_pem(key_material: str | bytes) -> bool:
    if isinstance(key_material, bytes):
        return key_material.strip().startswith(b"-----BEGIN")
    return key_material.strip().startswith("-----BEGIN")


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("Invalid signature encoding")
    if "=" in value:
        raise ValueError("Invalid signature encoding")
    padded = value.encode("ascii") + b"=" * (-len(value) % 4)
    decoded = base64.urlsafe_b64decode(padded)
    if _base64url_encode(decoded) != value:
        raise ValueError("Invalid signature encoding")
    return decoded
