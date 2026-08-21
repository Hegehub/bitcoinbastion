"""Access Certificate issuing service for Bastion Proof-of-Access Auth.

The issuer creates signed access-right metadata after verified payment or an
explicitly enabled manual grant. It never stores the raw Access Pass, never
accepts Bitcoin seed/private-key material, and does not create sessions or make
certificates sufficient for protected API access.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessCertificateStatus, AccessPaymentIntent
from app.domain.access.entitlements import get_plan_scopes
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.domain.access.scopes import FORBIDDEN_SCOPES
from app.services.access.crypto.exceptions import MissingIssuerKey
from app.services.access.crypto.hashing import (
    access_pass_commitment,
    access_pass_lookup_hash,
    canonical_json,
    certificate_fingerprint,
    constant_time_equal,
    reject_forbidden_secret_keys,
    sha256_prefixed,
)
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
    verify_serialized_issuer_envelope,
)
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy
from app.services.access.crypto.signatures import (
    sign_access_certificate,
    verify_access_certificate_signature,
)
from app.services.access.pass_generator import generate_raw_access_pass
from app.services.access.payments.base import PAYMENT_STATUS_PAID

CERTIFICATE_TYPE = "bastion_access_certificate"
CERTIFICATE_VERSION = 1
PRINCIPAL_BOUND_CERTIFICATE_VERSION = 2
DEFAULT_CERTIFICATE_TTL_DAYS = 365
PAID_PAYMENT_STATUSES = frozenset({PAYMENT_STATUS_PAID, "settled"})
SAVE_WARNING = (
    "Save this Bastion Access Pass now. It will not be shown again. "
    "This is not a Bitcoin wallet seed or Bitcoin private key."
)

AuditEmitter = Callable[[str, dict[str, Any]], None]


class AccessCertificateIssuerError(RuntimeError):
    """Base class for safe issuer errors."""


class PaymentNotSettledError(AccessCertificateIssuerError):
    """Raised when a payment intent has not been verified as paid."""


class ManualGrantDisabledError(AccessCertificateIssuerError):
    """Raised when manual certificate issuance is not explicitly enabled."""


class MissingDeviceKeyError(AccessCertificateIssuerError):
    """Raised when device public-key material/fingerprint is absent."""


class CertificateAlreadyIssuedError(AccessCertificateIssuerError):
    """Raised when a payment intent already produced a certificate."""


class IssuerKeyUnavailableError(AccessCertificateIssuerError):
    """Raised when issuer signing material is missing."""


class SignatureFailedError(AccessCertificateIssuerError):
    """Raised when certificate signing or verification fails."""


class UnsafeScopeDetectedError(AccessCertificateIssuerError):
    """Raised when plan scopes contain forbidden broad permissions."""


class PassGenerationFailedError(AccessCertificateIssuerError):
    """Raised when raw Access Pass generation fails."""


@dataclass(frozen=True, slots=True)
class AccessCertificateIssueResult:
    raw_access_pass: str
    access_certificate: dict[str, Any]
    certificate_fingerprint: str
    plan_code: PlanCode
    expires_at: datetime
    save_warning: str = SAVE_WARNING


class AccessCertificateIssuer:
    def __init__(
        self,
        db: Session,
        *,
        server_pepper: str,
        issuer_private_key: str,
        issuer_key_id: str,
        issuer_public_key: str | None = None,
        crypto_epoch: int = 1,
        certificate_ttl_days: int = DEFAULT_CERTIFICATE_TTL_DAYS,
        allow_manual_grants: bool = False,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        if not server_pepper:
            raise ValueError("ACCESS_SERVER_PEPPER is required for Access Pass lookup hashes")
        if not issuer_private_key or not issuer_key_id:
            raise IssuerKeyUnavailableError("Access issuer signing key configuration is missing")
        self.db = db
        self.server_pepper = server_pepper
        self.issuer_private_key = issuer_private_key
        self.issuer_key_id = issuer_key_id
        self.issuer_public_key = issuer_public_key
        self.crypto_epoch = crypto_epoch
        self.certificate_ttl_days = certificate_ttl_days
        self.allow_manual_grants = allow_manual_grants
        self.audit_emitter = audit_emitter

    def issue_certificate_for_checkout(
        self,
        *,
        payment_intent: AccessPaymentIntent,
        device_public_key: str,
        device_key_fingerprint: str,
        scopes: list[str],
        expires_at: datetime,
    ) -> AccessCertificateIssueResult:
        """Issue from an already-authorized frozen Checkout context."""
        if payment_intent.status not in PAID_PAYMENT_STATUSES:
            raise PaymentNotSettledError("Payment intent is not settled")
        return self._issue(
            plan_code=normalize_plan_code(payment_intent.plan_code),
            device_public_key=device_public_key,
            device_key_fingerprint=device_key_fingerprint,
            device_class="browser",
            payment_intent=payment_intent,
            scopes_override=scopes,
            expires_at_override=expires_at,
        )

    def issue_certificate_for_paid_intent(
        self,
        payment_intent_id: int,
        *,
        device_public_key: str | None = None,
        device_key_fingerprint: str | None = None,
        device_class: str = "unknown",
    ) -> AccessCertificateIssueResult:
        intent = self.db.get(AccessPaymentIntent, payment_intent_id)
        if intent is None or intent.status not in PAID_PAYMENT_STATUSES:
            raise PaymentNotSettledError("Payment intent is not settled")
        if (intent.metadata_json or {}).get("access_certificate_fingerprint"):
            raise CertificateAlreadyIssuedError(
                "Payment intent already issued an Access Certificate"
            )
        result = self._issue(
            plan_code=normalize_plan_code(intent.plan_code),
            device_public_key=device_public_key,
            device_key_fingerprint=device_key_fingerprint,
            device_class=device_class,
            payment_intent=intent,
        )
        metadata = dict(intent.metadata_json or {})
        metadata["access_certificate_fingerprint"] = result.certificate_fingerprint
        intent.metadata_json = metadata
        self.db.flush()
        return result

    def issue_certificate_for_manual_grant(
        self,
        plan_code: PlanCode | str,
        *,
        device_public_key: str | None = None,
        device_key_fingerprint: str | None = None,
        device_class: str = "unknown",
    ) -> AccessCertificateIssueResult:
        if not self.allow_manual_grants:
            raise ManualGrantDisabledError("Manual Access Certificate grants are disabled")
        return self._issue(
            plan_code=normalize_plan_code(plan_code),
            device_public_key=device_public_key,
            device_key_fingerprint=device_key_fingerprint,
            device_class=device_class,
            payment_intent=None,
        )

    def issue_principal_bound_certificate(
        self,
        plan_code: PlanCode | str,
        *,
        device_key_fingerprint: str,
        device_class: str,
        scopes: list[str],
        expires_at: datetime,
        principal_binding: dict[str, Any],
        subscription_binding: dict[str, Any],
        authorization: dict[str, Any],
        assurance: dict[str, Any],
        policy_epoch: int,
        schema_epoch: int = 2,
    ) -> AccessCertificateIssueResult:
        """Issue through the existing signer with bridge-calculated permissions."""
        return self._issue(
            plan_code=normalize_plan_code(plan_code),
            device_public_key=None,
            device_key_fingerprint=device_key_fingerprint,
            device_class=device_class,
            payment_intent=None,
            scopes_override=scopes,
            expires_at_override=expires_at,
            payload_extensions={
                "version": PRINCIPAL_BOUND_CERTIFICATE_VERSION,
                "principal_binding": principal_binding,
                "device_binding": {
                    "device_key_fingerprint": device_key_fingerprint,
                    "device_class": device_class,
                    "binding_status": "active",
                    "hardware_backed": bool(assurance.get("hardware_backed", False)),
                },
                "subscription_binding": subscription_binding,
                "authorization": authorization,
                "assurance": assurance,
                "policy_epoch": policy_epoch,
                "schema_epoch": schema_epoch,
                "signature_suite": "ed25519",
            },
        )

    def build_certificate_payload(
        self,
        *,
        pass_commitment: str,
        plan_code: PlanCode,
        device_key_fingerprint: str,
        device_public_key: str | None,
        scopes: list[str],
        issued_at: datetime,
        expires_at: datetime,
        signature: dict[str, Any] | None = None,
        payload_extensions: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_payload = {
            "type": CERTIFICATE_TYPE,
            "version": CERTIFICATE_VERSION,
            "pass_commitment": pass_commitment,
            "plan_code": plan_code.value,
            "device_key_fingerprint": device_key_fingerprint,
            "public_keys": {"device_classical": device_public_key, "device_pq": None},
            "scopes": scopes,
            "issued_at": _isoformat(issued_at),
            "expires_at": _isoformat(expires_at),
            "crypto_epoch": self.crypto_epoch,
            "hash_suite": {"primary": "SHA-256", "secondary": "SHA3-256", "xof": "SHAKE256"},
            "issuer_key_id": self.issuer_key_id,
        }
        if payload_extensions:
            base_payload.update(dict(payload_extensions))
        fingerprint = self.compute_certificate_fingerprint(base_payload)
        payload = {**base_payload, "certificate_fingerprint": fingerprint}
        payload["issuer_signatures"] = signature or {
            "classical": None,
            "post_quantum": None,
            "backup_hash_based": None,
        }
        return payload

    def compute_pass_commitment(self, raw_access_pass: str) -> str:
        return access_pass_commitment(raw_access_pass)

    def compute_pass_lookup_hash(self, raw_access_pass: str) -> str:
        return access_pass_lookup_hash(self.server_pepper, raw_access_pass)

    def compute_certificate_fingerprint(self, certificate_payload: Mapping[str, Any]) -> str:
        return certificate_fingerprint(_fingerprint_payload(certificate_payload))

    def verify_certificate_payload(
        self, certificate_payload: dict[str, Any], public_key: str | None = None
    ) -> bool:
        classical = (certificate_payload.get("issuer_signatures") or {}).get("classical") or {}
        signature = classical.get("sig") or classical.get("signature")
        if not isinstance(signature, str):
            return False
        signing_payload = _signing_payload(certificate_payload)
        expected_fingerprint = self.compute_certificate_fingerprint(certificate_payload)
        actual_fingerprint = certificate_payload.get("certificate_fingerprint")
        if not isinstance(actual_fingerprint, str) or not constant_time_equal(
            actual_fingerprint, expected_fingerprint
        ):
            return False
        verification_key = public_key or self.issuer_public_key
        if verification_key is None:
            raise MissingIssuerKey("Issuer public key is required for certificate verification")
        legacy_valid = verify_access_certificate_signature(
            signing_payload, verification_key, signature
        ).valid
        if not legacy_valid:
            return False
        envelope = certificate_payload.get("issuer_envelope")
        if isinstance(envelope, Mapping):
            return verify_serialized_issuer_envelope(
                signing_payload,
                envelope,
                public_key=verification_key,
                expected_key_id=self.issuer_key_id,
            )
        return True

    def get_certificate_by_pass(self, raw_access_pass: str) -> AccessCertificate | None:
        lookup_hash = self.compute_pass_lookup_hash(raw_access_pass)
        statement = select(AccessCertificate).where(
            AccessCertificate.pass_lookup_hash == lookup_hash
        )
        return self.db.execute(statement).scalar_one_or_none()

    def rotate_certificate_status(
        self, certificate_fingerprint_value: str, status: str
    ) -> AccessCertificate:
        certificate = self._get_certificate_by_fingerprint(certificate_fingerprint_value)
        certificate.status = status
        certificate.updated_at = datetime.now(UTC)
        self.db.flush()
        return certificate

    def revoke_certificate_marker(self, certificate_fingerprint_value: str) -> AccessCertificate:
        return self.rotate_certificate_status(
            certificate_fingerprint_value, AccessCertificateStatus.REVOKED.value
        )

    def _issue(
        self,
        *,
        plan_code: PlanCode,
        device_public_key: str | None,
        device_key_fingerprint: str | None,
        device_class: str,
        payment_intent: AccessPaymentIntent | None,
        scopes_override: list[str] | None = None,
        expires_at_override: datetime | None = None,
        payload_extensions: Mapping[str, Any] | None = None,
    ) -> AccessCertificateIssueResult:
        device_fingerprint = self._device_fingerprint(device_public_key, device_key_fingerprint)
        scopes = sorted(
            set(scopes_override) if scopes_override is not None else get_plan_scopes(plan_code)
        )
        if set(scopes) & FORBIDDEN_SCOPES:
            raise UnsafeScopeDetectedError("Forbidden scope detected in plan entitlement") from None
        raw_access_pass = self._generate_pass(plan_code)
        pass_commitment = self.compute_pass_commitment(raw_access_pass)
        pass_lookup_hash = self.compute_pass_lookup_hash(raw_access_pass)
        issued_at = datetime.now(UTC)
        expires_at = expires_at_override or issued_at + timedelta(days=self.certificate_ttl_days)
        if expires_at <= issued_at:
            raise AccessCertificateIssuerError("Access Certificate expiry must be in the future")
        unsigned_payload = self.build_certificate_payload(
            pass_commitment=pass_commitment,
            plan_code=plan_code,
            device_key_fingerprint=device_fingerprint,
            device_public_key=device_public_key,
            scopes=scopes,
            issued_at=issued_at,
            expires_at=expires_at,
            payload_extensions=payload_extensions,
        )
        signing_payload = _signing_payload(unsigned_payload)
        try:
            issuer_signature = sign_access_certificate(
                signing_payload,
                self.issuer_private_key,
                self.issuer_key_id,
                self.crypto_epoch,
            )
        except Exception as exc:
            raise SignatureFailedError("Access Certificate signing failed") from exc
        signature_json = {
            "classical": {
                "alg": issuer_signature.alg,
                "key_id": issuer_signature.key_id,
                "crypto_epoch": issuer_signature.crypto_epoch,
                "sig": issuer_signature.signature,
                "public_key_fingerprint": issuer_signature.public_key_fingerprint,
            },
            "post_quantum": None,
            "backup_hash_based": None,
        }
        issuer_envelope = build_classical_issuer_envelope(
            signing_payload,
            object_type=BastionIssuedObjectType.ACCESS_CERTIFICATE,
            object_id_hash=pass_commitment,
            object_fingerprint=unsigned_payload["certificate_fingerprint"],
            issuer_key_id=self.issuer_key_id,
            issuer_private_key=self.issuer_private_key,
            crypto_epoch=self.crypto_epoch,
            expires_at=expires_at,
            requirement=SignatureRequirementPolicy.CLASSICAL_REQUIRED,
        )
        envelope_json = issuer_envelope.to_dict()
        final_extensions = {**(payload_extensions or {}), "issuer_envelope": envelope_json}
        certificate_payload = self.build_certificate_payload(
            pass_commitment=pass_commitment,
            plan_code=plan_code,
            device_key_fingerprint=device_fingerprint,
            device_public_key=device_public_key,
            scopes=scopes,
            issued_at=issued_at,
            expires_at=expires_at,
            signature=signature_json,
            payload_extensions=final_extensions,
        )
        certificate = AccessCertificate(
            pass_lookup_hash=pass_lookup_hash,
            pass_commitment=pass_commitment,
            certificate_fingerprint=certificate_payload["certificate_fingerprint"],
            plan_code=plan_code.value,
            status=AccessCertificateStatus.ACTIVE.value,
            device_key_fingerprint=device_fingerprint,
            issuer_key_id=self.issuer_key_id,
            crypto_epoch=self.crypto_epoch,
            hash_suite_json=certificate_payload["hash_suite"],
            scopes_json=scopes,
            public_keys_json={
                "device_classical": None,
                "device_pq": None,
                "device_class": device_class,
            },
            issuer_signature_json=signature_json,
            issuer_envelope_json=envelope_json,
            issuer_envelope_hash=sha256_prefixed(canonical_json(envelope_json)),
            signature_requirement_policy=issuer_envelope.required_signature_policy.value,
            crypto_assurance=issuer_envelope.assurance_level.value,
            requires_reissue=False,
            issued_at=issued_at,
            expires_at=expires_at,
            created_at=issued_at,
            updated_at=issued_at,
        )
        self.db.add(certificate)
        self.db.flush()
        self._emit_audit(certificate, payment_intent)
        return AccessCertificateIssueResult(
            raw_access_pass=raw_access_pass,
            access_certificate=certificate_payload,
            certificate_fingerprint=certificate.certificate_fingerprint,
            plan_code=plan_code,
            expires_at=expires_at,
        )

    def _generate_pass(self, plan_code: PlanCode) -> str:
        try:
            return generate_raw_access_pass(plan_code)
        except Exception as exc:
            raise PassGenerationFailedError("Access Pass generation failed") from exc

    def _device_fingerprint(
        self, device_public_key: str | None, device_key_fingerprint: str | None
    ) -> str:
        if device_key_fingerprint:
            return device_key_fingerprint
        if device_public_key:
            return sha256_prefixed(device_public_key)
        raise MissingDeviceKeyError("Device public key or fingerprint is required")

    def _get_certificate_by_fingerprint(
        self, certificate_fingerprint_value: str
    ) -> AccessCertificate:
        statement = select(AccessCertificate).where(
            AccessCertificate.certificate_fingerprint == certificate_fingerprint_value
        )
        certificate = self.db.execute(statement).scalar_one_or_none()
        if certificate is None:
            raise AccessCertificateIssuerError("Access Certificate not found")
        return certificate

    def _emit_audit(
        self, certificate: AccessCertificate, payment_intent: AccessPaymentIntent | None
    ) -> None:
        if self.audit_emitter is None:
            return
        payload = {
            "certificate_fingerprint": certificate.certificate_fingerprint,
            "plan_code": certificate.plan_code,
            "device_key_fingerprint": certificate.device_key_fingerprint,
            "issuer_key_id": certificate.issuer_key_id,
            "crypto_epoch": certificate.crypto_epoch,
            "payment_intent_id": payment_intent.id if payment_intent is not None else None,
            "issued_at": _isoformat(certificate.issued_at),
            "expires_at": _isoformat(certificate.expires_at),
        }
        reject_forbidden_secret_keys(payload)
        self.audit_emitter("certificate_issued", payload)


def _signing_payload(certificate_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        key: value
        for key, value in certificate_payload.items()
        if key not in {"issuer_signatures", "issuer_envelope"}
    }
    envelope = certificate_payload.get("issuer_envelope")
    if isinstance(envelope, Mapping) and isinstance(envelope.get("object_fingerprint"), str):
        payload["certificate_fingerprint"] = envelope["object_fingerprint"]
    return payload


def _fingerprint_payload(certificate_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in certificate_payload.items()
        if key not in {"issuer_signatures", "certificate_fingerprint"}
    }


def _isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
