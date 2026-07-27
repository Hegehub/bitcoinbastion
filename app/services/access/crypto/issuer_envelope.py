"""Unified truthful issuer envelope and signing/verification services."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hmac import compare_digest
from typing import Any, Callable, Mapping

from app.services.access.crypto.algorithms import (
    CryptoAssuranceLevel,
    CryptoCapabilityStatus,
    HashAlgorithm,
    SignatureAlgorithm,
)
from app.services.access.crypto.crypto_agility import (
    CryptoCapabilityRegistry,
    CryptoProviderUnavailable,
)
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.access.crypto.key_registry import (
    IssuerKeyRegistry,
    IssuerKeyUnavailable,
)
from app.services.access.crypto.migration_policy import (
    CryptoEpochRegistry,
    SignatureRequirementPolicy,
)
from app.services.access.crypto.signatures import Ed25519SignatureSuite


class BastionIssuedObjectType(StrEnum):
    WALLET_SUBSCRIPTION_ENTITLEMENT = "wallet_subscription_entitlement"
    LIGHTNING_SUBSCRIPTION_ENTITLEMENT = "lightning_subscription_entitlement"
    ACCESS_CERTIFICATE = "access_certificate"
    DELEGATED_PASS = "delegated_pass"
    CHILD_API_KEY_CREDENTIAL = "child_api_key_credential"
    RECOVERY_CAPSULE = "recovery_capsule"
    OFFLINE_VALIDITY_PACK = "offline_validity_pack"
    REVOCATION_EPOCH = "revocation_epoch"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    POLICY_CHECKPOINT = "policy_checkpoint"
    BUSINESS_ROLE_CREDENTIAL = "business_role_credential"
    PAYREGISTER_DEVICE_CREDENTIAL = "payregister_device_credential"
    LNURL_PAYMENT_PROOF_RECEIPT = "lnurl_payment_proof_receipt"
    LNURL_REFUND_AUTHORIZATION = "lnurl_refund_authorization"
    LNURL_WITHDRAW_AUTHORIZATION = "lnurl_withdraw_authorization"
    MERCHANT_RECEIPT_PACKET = "merchant_receipt_packet"


@dataclass(frozen=True, slots=True)
class EnvelopeSignature:
    alg: SignatureAlgorithm
    key_id: str | None
    sig: str | None
    status: CryptoCapabilityStatus

    def __post_init__(self) -> None:
        if self.status in {
            CryptoCapabilityStatus.ACTIVE,
            CryptoCapabilityStatus.SIGN_AND_VERIFY,
        } and (not self.key_id or not self.sig):
            raise ValueError("Operational signature requires key ID and signature")
        if self.sig is None and self.status not in {
            CryptoCapabilityStatus.METADATA_ONLY,
            CryptoCapabilityStatus.PLANNED,
            CryptoCapabilityStatus.DISABLED,
            CryptoCapabilityStatus.UNSUPPORTED,
        }:
            raise ValueError("Null signature status is contradictory")


@dataclass(frozen=True, slots=True)
class BastionIssuerSignatureEnvelope:
    type: str
    version: int
    object_type: BastionIssuedObjectType
    object_id_hash: str
    object_fingerprint: str
    canonicalization_version: int
    payload_hash: dict[str, str]
    issuer_key_id: str
    issuer_key_fingerprint: str
    issuer_domain: str
    crypto_epoch: int
    policy_epoch: int
    schema_epoch: int
    issued_at: str
    expires_at: str | None
    assurance_level: CryptoAssuranceLevel
    required_signature_policy: SignatureRequirementPolicy
    classical_signature: EnvelopeSignature | None
    post_quantum_signature: EnvelopeSignature | None
    root_signature: EnvelopeSignature | None
    migration_metadata: dict[str, Any]
    verification_metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if self.type != "bastion_issuer_signature_envelope" or self.version != 1:
            raise ValueError("Unsupported issuer envelope")
        if self.payload_hash.get("alg") != HashAlgorithm.SHA256.value or not self.payload_hash.get(
            "value"
        ):
            raise ValueError("Explicit supported payload hash is required")
        if not self.issuer_key_id or self.crypto_epoch < 1:
            raise ValueError("Issuer key and crypto epoch are required")
        pq_present = (
            self.post_quantum_signature is not None and self.post_quantum_signature.sig is not None
        )
        if (
            self.assurance_level
            in {CryptoAssuranceLevel.POST_QUANTUM, CryptoAssuranceLevel.HYBRID_TRANSITION}
            and not pq_present
        ):
            raise ValueError("PQ or hybrid assurance requires a real PQ signature")
        if self.required_signature_policy is SignatureRequirementPolicy.HYBRID_REQUIRED and (
            self.classical_signature is None or not pq_present
        ):
            raise ValueError("Hybrid policy requires classical and PQ signatures")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["object_type"] = self.object_type.value
        value["assurance_level"] = self.assurance_level.value
        value["required_signature_policy"] = self.required_signature_policy.value
        for field in ("classical_signature", "post_quantum_signature", "root_signature"):
            signature = value[field]
            if signature:
                signature["alg"] = signature["alg"].value
                signature["status"] = signature["status"].value
        value["issuer"] = {
            "key_id": value.pop("issuer_key_id"),
            "key_fingerprint": value.pop("issuer_key_fingerprint"),
            "domain": value.pop("issuer_domain"),
        }
        value["epochs"] = {
            "crypto": value.pop("crypto_epoch"),
            "policy": value.pop("policy_epoch"),
            "schema": value.pop("schema_epoch"),
        }
        value["signatures"] = {
            "classical": value.pop("classical_signature"),
            "post_quantum": value.pop("post_quantum_signature"),
            "root": value.pop("root_signature"),
        }
        value["migration"] = value.pop("migration_metadata")
        value["verification"] = value.pop("verification_metadata")
        return value


@dataclass(frozen=True, slots=True)
class IssuerEnvelopeVerificationResult:
    verified: bool
    object_fingerprint_valid: bool
    payload_hash_valid: bool
    classical_signature_valid: bool
    post_quantum_signature_present: bool
    post_quantum_signature_valid: bool
    root_signature_valid: bool
    required_policy_satisfied: bool
    issuer_key_status: str
    crypto_epoch_supported: bool
    assurance_level_granted: CryptoAssuranceLevel
    requires_reissue: bool
    warnings: tuple[str, ...] = ()
    failure_reason: str | None = None


class BastionIssuerSigningService:
    def __init__(
        self,
        *,
        capabilities: CryptoCapabilityRegistry,
        keys: IssuerKeyRegistry,
        epochs: CryptoEpochRegistry,
        private_key_resolver: Callable[[str], str],
        issuer_domain: str = "bitcoin-bastion.com",
    ) -> None:
        self.capabilities, self.keys, self.epochs = capabilities, keys, epochs
        self.private_key_resolver, self.issuer_domain = private_key_resolver, issuer_domain

    def sign(
        self,
        payload: Mapping[str, Any],
        *,
        object_type: BastionIssuedObjectType,
        object_id_hash: str,
        object_fingerprint: str,
        issuer_key_id: str,
        policy_epoch: int = 1,
        schema_epoch: int = 1,
        expires_at: datetime | None = None,
        requirement: SignatureRequirementPolicy | None = None,
    ) -> BastionIssuerSignatureEnvelope:
        epoch = self.epochs.active()
        requirement = requirement or epoch.requirement_for(object_type.value)
        if requirement in {
            SignatureRequirementPolicy.HYBRID_REQUIRED,
            SignatureRequirementPolicy.PQ_REQUIRED,
            SignatureRequirementPolicy.LONG_TERM_ROOT_REQUIRED,
        }:
            raise CryptoProviderUnavailable("Required PQ/root signing capability is unavailable")
        key = self.keys.resolve_for_signing(issuer_key_id, object_type.value)
        self.capabilities.require_signing(key.algorithm)
        canonical_payload = dict(payload)
        payload_hash = sha256_prefixed(canonical_json(canonical_payload))
        claims = _envelope_signing_claims(
            object_type,
            object_id_hash,
            object_fingerprint,
            payload_hash,
            epoch.epoch,
            policy_epoch,
            schema_epoch,
            requirement,
        )
        signature = Ed25519SignatureSuite().sign(
            claims,
            "issuer_envelope",
            key.key_id,
            self.private_key_resolver(key.private_key_provider_reference or ""),
            epoch.epoch,
        )
        pq = EnvelopeSignature(
            SignatureAlgorithm.ML_DSA_65, None, None, CryptoCapabilityStatus.METADATA_ONLY
        )
        return BastionIssuerSignatureEnvelope(
            "bastion_issuer_signature_envelope",
            1,
            object_type,
            object_id_hash,
            object_fingerprint,
            1,
            {"alg": HashAlgorithm.SHA256.value, "value": payload_hash},
            key.key_id,
            key.key_fingerprint,
            self.issuer_domain,
            epoch.epoch,
            policy_epoch,
            schema_epoch,
            _iso(datetime.now(UTC)),
            _iso(expires_at) if expires_at else None,
            CryptoAssuranceLevel.CLASSICAL,
            requirement,
            EnvelopeSignature(
                SignatureAlgorithm.ED25519,
                key.key_id,
                signature.signature,
                CryptoCapabilityStatus.ACTIVE,
            ),
            pq,
            None,
            {
                "target_crypto_epoch": 2,
                "target_policy": "hybrid_required",
                "must_reissue_before": None,
            },
            {"canonicalization_version": 1, "pq_provider_operational": False},
        )


class BastionIssuerVerificationService:
    def __init__(
        self,
        *,
        capabilities: CryptoCapabilityRegistry,
        keys: IssuerKeyRegistry,
        epochs: CryptoEpochRegistry,
        public_key_resolver: Callable[[str], str],
    ) -> None:
        self.capabilities, self.keys, self.epochs, self.public_key_resolver = (
            capabilities,
            keys,
            epochs,
            public_key_resolver,
        )

    def verify(
        self, payload: Mapping[str, Any], envelope: BastionIssuerSignatureEnvelope
    ) -> IssuerEnvelopeVerificationResult:
        payload_hash = sha256_prefixed(canonical_json(dict(payload)))
        hash_valid = compare_digest(payload_hash, envelope.payload_hash["value"])
        fingerprint_valid = bool(envelope.object_fingerprint.startswith("sha256:"))
        epoch = self.epochs.get(envelope.crypto_epoch)
        if epoch is None or epoch.status != "active":
            return _failed("unsupported_crypto_epoch", hash_valid, fingerprint_valid)
        try:
            key = self.keys.resolve_for_verification(envelope.issuer_key_id)
        except IssuerKeyUnavailable as exc:
            return _failed(
                str(exc),
                hash_valid,
                fingerprint_valid,
                issuer_status="unavailable",
                requires_reissue=True,
            )
        classical = envelope.classical_signature
        classical_valid = False
        if classical and classical.alg is SignatureAlgorithm.ED25519 and classical.sig:
            self.capabilities.require_verification(classical.alg)
            classical_valid = (
                Ed25519SignatureSuite()
                .verify(
                    _envelope_signing_claims(
                        envelope.object_type,
                        envelope.object_id_hash,
                        envelope.object_fingerprint,
                        envelope.payload_hash["value"],
                        envelope.crypto_epoch,
                        envelope.policy_epoch,
                        envelope.schema_epoch,
                        envelope.required_signature_policy,
                    ),
                    "issuer_envelope",
                    self.public_key_resolver(key.public_key_reference),
                    classical.sig,
                )
                .valid
            )
        pq = envelope.post_quantum_signature
        pq_present = pq is not None and pq.sig is not None
        pq_valid = False
        if pq_present:
            assert pq is not None
            try:
                self.capabilities.require_verification(pq.alg)
            except CryptoProviderUnavailable:
                return _failed(
                    "pq_provider_unavailable", hash_valid, fingerprint_valid, classical_valid, True
                )
        policy = envelope.required_signature_policy
        satisfied = (
            classical_valid
            if policy
            in {
                SignatureRequirementPolicy.CLASSICAL_REQUIRED,
                SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
                SignatureRequirementPolicy.VERIFY_LEGACY_THEN_REISSUE,
            }
            else False
        )
        verified = hash_valid and fingerprint_valid and satisfied
        assurance = CryptoAssuranceLevel.CLASSICAL if verified else CryptoAssuranceLevel.CLASSICAL
        return IssuerEnvelopeVerificationResult(
            verified,
            fingerprint_valid,
            hash_valid,
            classical_valid,
            pq_present,
            pq_valid,
            False,
            satisfied,
            key.status.value,
            True,
            assurance,
            policy is SignatureRequirementPolicy.VERIFY_LEGACY_THEN_REISSUE,
            () if verified else ("policy_unsatisfied",),
            None if verified else "required_signature_policy_unsatisfied",
        )


def _failed(
    reason: str,
    hash_valid: bool,
    fingerprint_valid: bool,
    classical: bool = False,
    pq_present: bool = False,
    issuer_status: str = "unknown",
    requires_reissue: bool = False,
) -> IssuerEnvelopeVerificationResult:
    return IssuerEnvelopeVerificationResult(
        False,
        fingerprint_valid,
        hash_valid,
        classical,
        pq_present,
        False,
        False,
        False,
        issuer_status,
        False,
        CryptoAssuranceLevel.CLASSICAL,
        requires_reissue,
        (),
        reason,
    )


def build_classical_issuer_envelope(
    payload: Mapping[str, Any],
    *,
    object_type: BastionIssuedObjectType,
    object_id_hash: str,
    object_fingerprint: str,
    issuer_key_id: str,
    issuer_private_key: str,
    issuer_domain: str = "bitcoin-bastion.com",
    crypto_epoch: int = 1,
    policy_epoch: int = 1,
    schema_epoch: int = 1,
    expires_at: datetime | None = None,
    requirement: SignatureRequirementPolicy = SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
) -> BastionIssuerSignatureEnvelope:
    """Compatibility helper for existing issuers migrating to the shared envelope."""
    if crypto_epoch != 1:
        raise CryptoProviderUnavailable("Only crypto epoch 1 is operational")
    if requirement in {
        SignatureRequirementPolicy.HYBRID_REQUIRED,
        SignatureRequirementPolicy.PQ_REQUIRED,
        SignatureRequirementPolicy.LONG_TERM_ROOT_REQUIRED,
    }:
        raise CryptoProviderUnavailable("Required PQ/root signing capability is unavailable")
    canonical_payload = dict(payload)
    payload_hash = sha256_prefixed(canonical_json(canonical_payload))
    claims = _envelope_signing_claims(
        object_type,
        object_id_hash,
        object_fingerprint,
        payload_hash,
        crypto_epoch,
        policy_epoch,
        schema_epoch,
        requirement,
    )
    signature = Ed25519SignatureSuite().sign(
        claims, "issuer_envelope", issuer_key_id, issuer_private_key, crypto_epoch
    )
    return BastionIssuerSignatureEnvelope(
        "bastion_issuer_signature_envelope",
        1,
        object_type,
        object_id_hash,
        object_fingerprint,
        1,
        {"alg": HashAlgorithm.SHA256.value, "value": payload_hash},
        issuer_key_id,
        signature.public_key_fingerprint or "sha256:unknown",
        issuer_domain,
        crypto_epoch,
        policy_epoch,
        schema_epoch,
        _iso(datetime.now(UTC)),
        _iso(expires_at) if expires_at else None,
        CryptoAssuranceLevel.CLASSICAL,
        requirement,
        EnvelopeSignature(
            SignatureAlgorithm.ED25519,
            issuer_key_id,
            signature.signature,
            CryptoCapabilityStatus.ACTIVE,
        ),
        EnvelopeSignature(
            SignatureAlgorithm.ML_DSA_65,
            None,
            None,
            CryptoCapabilityStatus.METADATA_ONLY,
        ),
        None,
        {
            "target_crypto_epoch": 2,
            "target_policy": "hybrid_required",
            "must_reissue_before": None,
        },
        {"canonicalization_version": 1, "pq_provider_operational": False},
    )


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _envelope_signing_claims(
    object_type: BastionIssuedObjectType,
    object_id_hash: str,
    object_fingerprint: str,
    payload_hash: str,
    crypto_epoch: int,
    policy_epoch: int,
    schema_epoch: int,
    requirement: SignatureRequirementPolicy,
) -> dict[str, Any]:
    return {
        "type": "bastion_issuer_signature_claims",
        "version": 1,
        "object_type": object_type.value,
        "object_id_hash": object_id_hash,
        "object_fingerprint": object_fingerprint,
        "canonicalization_version": 1,
        "payload_hash": {"alg": "sha256", "value": payload_hash},
        "epochs": {"crypto": crypto_epoch, "policy": policy_epoch, "schema": schema_epoch},
        "required_signature_policy": requirement.value,
    }


def verify_serialized_issuer_envelope(
    payload: Mapping[str, Any],
    envelope: Mapping[str, Any],
    *,
    public_key: str,
    expected_key_id: str | None = None,
) -> bool:
    """Compatibility verifier for envelope JSON stored beside legacy signatures."""
    try:
        if (
            envelope.get("type") != "bastion_issuer_signature_envelope"
            or envelope.get("version") != 1
        ):
            return False
        payload_hash = sha256_prefixed(canonical_json(dict(payload)))
        hash_data = envelope.get("payload_hash")
        if (
            not isinstance(hash_data, Mapping)
            or hash_data.get("alg") != "sha256"
            or not compare_digest(payload_hash, str(hash_data.get("value", "")))
        ):
            return False
        issuer = envelope.get("issuer")
        epochs = envelope.get("epochs")
        signatures = envelope.get("signatures")
        if (
            not isinstance(issuer, Mapping)
            or not isinstance(epochs, Mapping)
            or not isinstance(signatures, Mapping)
        ):
            return False
        key_id = str(issuer.get("key_id", ""))
        if not key_id or (expected_key_id and key_id != expected_key_id):
            return False
        policy = SignatureRequirementPolicy(str(envelope.get("required_signature_policy")))
        classical = signatures.get("classical")
        pq = signatures.get("post_quantum")
        if (
            not isinstance(classical, Mapping)
            or classical.get("alg") != "ed25519"
            or not isinstance(classical.get("sig"), str)
        ):
            return False
        if isinstance(pq, Mapping) and pq.get("sig") is not None:
            return False  # No operational PQ verifier exists; supplied material fails closed.
        if policy not in {
            SignatureRequirementPolicy.CLASSICAL_REQUIRED,
            SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
            SignatureRequirementPolicy.VERIFY_LEGACY_THEN_REISSUE,
        }:
            return False
        crypto_epoch = epochs.get("crypto")
        policy_epoch = epochs.get("policy")
        schema_epoch = epochs.get("schema")
        if not all(isinstance(value, int) for value in (crypto_epoch, policy_epoch, schema_epoch)):
            return False
        assert isinstance(crypto_epoch, int)
        assert isinstance(policy_epoch, int)
        assert isinstance(schema_epoch, int)
        claims = _envelope_signing_claims(
            BastionIssuedObjectType(str(envelope.get("object_type"))),
            str(envelope.get("object_id_hash")),
            str(envelope.get("object_fingerprint")),
            payload_hash,
            crypto_epoch,
            policy_epoch,
            schema_epoch,
            policy,
        )
        return (
            Ed25519SignatureSuite()
            .verify(claims, "issuer_envelope", public_key, str(classical.get("sig")))
            .valid
        )
    except (KeyError, TypeError, ValueError):
        return False
