"""Policy-enforced bridge from Wallet/LNURL principals to Access Certificates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import (
    AccessCertificate,
    AccessCertificatePrincipalBinding,
    AccessCertificateStatus,
    SubscriptionEntitlement,
    SubscriptionEntitlementStatus,
)
from app.db.models.wallet_auth import WalletDevice, WalletPrincipal, WalletSession
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.certificate_issuer import AccessCertificateIssuer
from app.services.access.entitlement_service import SubscriptionEntitlementService
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine, POLICY_DECISION_ALLOW


class PrincipalCertificateBridgeError(ValueError):
    """Enumeration-safe, machine-readable bridge failure."""


class CertificateAssuranceProfile(StrEnum):
    COMPATIBILITY = "compatibility"
    STANDARD = "standard"
    HIGH_ASSURANCE = "high_assurance"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SOVEREIGN = "sovereign"


class LegacyCertificateClass(StrEnum):
    LEGACY_UNBOUND = "legacy_unbound"
    LEGACY_DEVICE_BOUND = "legacy_device_bound"
    LEGACY_ENTITLEMENT_BOUND = "legacy_entitlement_bound"
    MIGRATED_PRINCIPAL_BOUND = "migrated_principal_bound"
    REVOKED = "revoked"


SUPPORTED_PRINCIPAL_TYPES = frozenset(
    {
        "bitcoin_wallet_principal",
        "lightning_wallet_principal",
        "multi_method_principal",
        "business_owner_principal",
        "enterprise_principal",
        "payregister_owner_principal",
    }
)
TREASURY_SCOPES = frozenset(
    {
        "treasury:read",
        "treasury:write",
        "treasury:policy:manage",
        "descriptor:manage",
        "onchain:ownership",
    }
)
HIGH_ASSURANCE_PROFILES = frozenset(
    {
        CertificateAssuranceProfile.HIGH_ASSURANCE,
        CertificateAssuranceProfile.BUSINESS,
        CertificateAssuranceProfile.ENTERPRISE,
        CertificateAssuranceProfile.SOVEREIGN,
    }
)


@dataclass(frozen=True, slots=True)
class PrincipalCertificateIssueRequest:
    principal_hash: str
    principal_type: str
    device_key_fingerprint: str
    entitlement_id: int
    session_hash: str
    proof_method: str
    verification_strength: str
    last_principal_verification_at: datetime
    requested_scopes: frozenset[str]
    requested_metric_groups: frozenset[str]
    policy_allowed_scopes: frozenset[str]
    policy_allowed_metric_groups: frozenset[str]
    principal_allowed_scopes: frozenset[str]
    requested_assurance_profile: CertificateAssuranceProfile
    requested_expires_at: datetime
    idempotency_key_hash: str
    proof_freshness_seconds: int | None = None
    delegation_requested: bool = False
    offline_pack_requested: bool = False
    step_up_satisfied: bool = False
    quorum_satisfied: bool = False
    human_intent_verified: bool = False
    business_role: str | None = None
    recovery_state: str | None = None
    lockdown_state: str | None = None
    principal_revocation_epoch: int = 0
    policy_epoch: int = 1
    crypto_epoch: int = 1
    hardware_evidence_verified: bool = False
    export_requested: bool = False
    rotation_of: str | None = None
    pop_request_verified: bool = False
    auth_domain_verified: bool = False


@dataclass(frozen=True, slots=True)
class PrincipalCertificatePolicyDecision:
    decision: str
    reason_code: str
    policy_hash: str
    allowed_scopes: frozenset[str]
    allowed_metric_groups: frozenset[str]
    assurance_profile: CertificateAssuranceProfile


@dataclass(frozen=True, slots=True)
class PrincipalCertificateResult:
    certificate_fingerprint: str
    principal_binding_hash: str
    principal_type: str
    assurance_profile: CertificateAssuranceProfile
    effective_scopes: tuple[str, ...]
    effective_metric_groups: tuple[str, ...]
    expires_at: datetime
    certificate_payload: dict[str, Any]
    export_payload: dict[str, Any] | None = None
    idempotent_replay: bool = False
    limitations: tuple[str, ...] = (
        "not_bearer_access",
        "active_principal_device_session_entitlement_policy_and_revocation_required",
    )


class PrincipalCertificatePolicy(Protocol):
    def evaluate(
        self, request: PrincipalCertificateIssueRequest
    ) -> PrincipalCertificatePolicyDecision: ...


class PrincipalCertificateRevocationResolver(Protocol):
    def check_certificate_bridge_targets(self, **targets: str | None) -> Mapping[str, object]: ...


MetricEmitter = Callable[[str, dict[str, str]], None]


class AccessPolicyEngineCertificatePolicy:
    """Adapter retaining the existing Access Policy Engine as final authority."""

    def __init__(
        self,
        engine: AccessPolicyEngine,
        context_factory: Callable[[PrincipalCertificateIssueRequest], AccessPolicyContext],
    ) -> None:
        self.engine, self.context_factory = engine, context_factory

    def evaluate(
        self, request: PrincipalCertificateIssueRequest
    ) -> PrincipalCertificatePolicyDecision:
        decision = self.engine.evaluate(self.context_factory(request))
        allowed_scopes = decision.metadata.get("allowed_scopes", request.policy_allowed_scopes)
        allowed_metrics = decision.metadata.get(
            "allowed_metric_groups", request.policy_allowed_metric_groups
        )
        return PrincipalCertificatePolicyDecision(
            decision.decision,
            decision.reason_code,
            decision.policy_hash or request.idempotency_key_hash,
            frozenset(str(item) for item in allowed_scopes),
            frozenset(str(item) for item in allowed_metrics),
            request.requested_assurance_profile,
        )


class PrincipalAccessCertificateBridge:
    def __init__(
        self,
        db: Session,
        *,
        issuer: AccessCertificateIssuer,
        entitlement_service: SubscriptionEntitlementService,
        policy: PrincipalCertificatePolicy,
        revocation_resolver: PrincipalCertificateRevocationResolver,
        audit_chain: AccessAuditChain | None = None,
        metric_emitter: MetricEmitter | None = None,
        export_enabled: bool = False,
        default_ttl_seconds: int = 86400,
        max_ttl_seconds: int = 2592000,
        supported_crypto_epochs: frozenset[int] = frozenset({1}),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db, self.issuer, self.entitlement_service, self.policy = (
            db,
            issuer,
            entitlement_service,
            policy,
        )
        self.revocations = revocation_resolver
        self.audit = audit_chain or AccessAuditChain(db)
        self.metric_emitter, self.export_enabled = metric_emitter, export_enabled
        self.default_ttl_seconds, self.max_ttl_seconds = default_ttl_seconds, max_ttl_seconds
        self.supported_crypto_epochs = supported_crypto_epochs
        self.clock = clock or (lambda: datetime.now(UTC))

    def issue(self, request: PrincipalCertificateIssueRequest) -> PrincipalCertificateResult:
        self._validate_request(request)
        existing = self._idempotent_result(request)
        if existing:
            return replace(existing, idempotent_replay=True)
        with self.db.begin_nested():
            principal = self._principal(request)
            device = self._device(request)
            session = self._session(request)
            entitlement = self._entitlement(request)
            self._check_revocations(request, principal, device, session, entitlement)
            policy = self.policy.evaluate(request)
            self._audit_request(request, policy)
            if policy.decision != POLICY_DECISION_ALLOW:
                self._metric(request, policy.decision, policy.reason_code)
                raise PrincipalCertificateBridgeError(policy.reason_code or "policy_denied")
            effective_scopes = (
                request.requested_scopes
                & request.principal_allowed_scopes
                & frozenset(_strings(entitlement.scopes_json))
                & policy.allowed_scopes
            )
            entitlement_metrics = frozenset(
                str(key) for key in entitlement.metric_entitlements_json
            )
            effective_metrics = (
                request.requested_metric_groups & entitlement_metrics & policy.allowed_metric_groups
            )
            if effective_scopes != request.requested_scopes:
                raise PrincipalCertificateBridgeError("scope_not_allowed")
            if effective_metrics != request.requested_metric_groups:
                raise PrincipalCertificateBridgeError("metric_not_allowed")
            expires_at = min(
                _utc(request.requested_expires_at),
                _utc(entitlement.valid_until),
                self.clock() + timedelta(seconds=self.max_ttl_seconds),
            )
            if expires_at <= self.clock():
                raise PrincipalCertificateBridgeError("entitlement_expired")
            entitlement_fingerprint = _entitlement_fingerprint(entitlement)
            binding_payload = {
                "principal_type": request.principal_type,
                "principal_hash": request.principal_hash,
                "device_key_fingerprint": request.device_key_fingerprint,
                "entitlement_fingerprint": entitlement_fingerprint,
                "policy_hash": policy.policy_hash,
                "crypto_epoch": request.crypto_epoch,
            }
            principal_binding_hash = sha256_prefixed(canonical_json(binding_payload))
            principal_binding = {
                "principal_type": request.principal_type,
                "principal_hash": request.principal_hash,
                "principal_binding_hash": principal_binding_hash,
                "proof_method": request.proof_method,
                "verification_strength": request.verification_strength,
                "last_verified_at": _iso(request.last_principal_verification_at),
                "principal_policy_epoch": principal.policy_epoch,
                "principal_revocation_epoch": request.principal_revocation_epoch,
            }
            authorization = {
                "scopes": sorted(effective_scopes),
                "metric_groups": sorted(effective_metrics),
                "delegation_allowed": request.delegation_requested,
                "offline_pack_allowed": request.offline_pack_requested,
                "max_session_ttl_seconds": 900,
            }
            assurance = {
                "profile": policy.assurance_profile.value,
                "hardware_backed": bool(request.hardware_evidence_verified),
                "requires_principal_active": True,
                "requires_device_binding": True,
                "requires_pop_session": True,
                "requires_policy_decision": True,
                "requires_fresh_step_up_for_critical_actions": True,
            }
            subscription_binding = {
                "entitlement_fingerprint": entitlement_fingerprint,
                "plan": entitlement.plan_code,
                "status": entitlement.status,
                "valid_until": _iso(entitlement.valid_until),
                "metric_entitlement_hash": sha256_prefixed(
                    canonical_json(entitlement.metric_entitlements_json)
                ),
            }
            # Recheck immediately before signing to close state-change races.
            self._check_revocations(request, principal, device, session, entitlement)
            issued = self.issuer.issue_principal_bound_certificate(
                entitlement.plan_code,
                device_key_fingerprint=request.device_key_fingerprint,
                device_class=device.device_class,
                scopes=sorted(effective_scopes),
                expires_at=expires_at,
                principal_binding=principal_binding,
                subscription_binding=subscription_binding,
                authorization=authorization,
                assurance=assurance,
                policy_epoch=request.policy_epoch,
            )
            certificate = self.db.execute(
                select(AccessCertificate).where(
                    AccessCertificate.certificate_fingerprint == issued.certificate_fingerprint
                )
            ).scalar_one()
            certificate_entitlement = self.entitlement_service.issue_entitlement(
                pass_lookup_hash=certificate.pass_lookup_hash,
                certificate_fingerprint=certificate.certificate_fingerprint,
                plan_code=entitlement.plan_code,
                valid_from=self.clock(),
                valid_until=expires_at,
                metadata={
                    "principal_hash": request.principal_hash,
                    "source_entitlement_id": entitlement.id,
                    "principal_certificate_bridge": True,
                },
            )
            binding = AccessCertificatePrincipalBinding(
                certificate_id=certificate.id,
                certificate_fingerprint=certificate.certificate_fingerprint,
                principal_hash=request.principal_hash,
                principal_type=request.principal_type,
                principal_binding_hash=principal_binding_hash,
                proof_method=request.proof_method,
                verification_strength=request.verification_strength,
                device_key_fingerprint=request.device_key_fingerprint,
                entitlement_fingerprint=entitlement_fingerprint,
                assurance_profile=policy.assurance_profile.value,
                policy_epoch=request.policy_epoch,
                principal_revocation_epoch=request.principal_revocation_epoch,
                crypto_epoch=request.crypto_epoch,
                status="active",
                metadata_json={
                    "idempotency_key_hash": request.idempotency_key_hash,
                    "certificate_payload": issued.access_certificate,
                    "effective_metric_groups": sorted(effective_metrics),
                    "entitlement_id": certificate_entitlement.id,
                    "source_entitlement_id": entitlement.id,
                    "wallet_bound": request.principal_type != "lightning_wallet_principal",
                    "lnurl_bound": request.principal_type == "lightning_wallet_principal",
                    "legacy_class": LegacyCertificateClass.MIGRATED_PRINCIPAL_BOUND.value,
                },
                created_at=self.clock(),
                updated_at=self.clock(),
            )
            self.db.add(binding)
            if request.rotation_of:
                old = self._certificate(request.rotation_of)
                old.status = AccessCertificateStatus.REVOKED.value
                old.replaced_by_certificate_fingerprint = certificate.certificate_fingerprint
                old_binding = self._binding(old.certificate_fingerprint)
                if old_binding is None:  # pragma: no cover - required lookup fails first
                    raise PrincipalCertificateBridgeError("certificate_rotation_required")
                old_binding.status = "revoked"
            self.db.flush()
            export = (
                self._build_export(binding, issued.access_certificate)
                if request.export_requested
                else None
            )
            result = PrincipalCertificateResult(
                certificate.certificate_fingerprint,
                principal_binding_hash,
                request.principal_type,
                policy.assurance_profile,
                tuple(sorted(effective_scopes)),
                tuple(sorted(effective_metrics)),
                expires_at,
                issued.access_certificate,
                export,
            )
            self._audit_lifecycle("principal_certificate_issued", binding, "issued")
            if export:
                self._audit_lifecycle("principal_certificate_exported", binding, "exported")
            self._metric(request, "allow", "issued")
            return result

    def inspect(self, certificate_fingerprint: str) -> dict[str, Any]:
        certificate = self._certificate(certificate_fingerprint)
        binding = self._binding(certificate_fingerprint, required=False)
        return {
            "certificate_fingerprint": certificate.certificate_fingerprint,
            "status": certificate.status,
            "expires_at": _iso(certificate.expires_at),
            "legacy_class": self.classify_legacy(certificate, binding).value,
            "principal_type": binding.principal_type if binding else None,
            "assurance_profile": binding.assurance_profile if binding else "compatibility",
            "device_key_fingerprint": binding.device_key_fingerprint if binding else None,
            "entitlement_fingerprint": binding.entitlement_fingerprint if binding else None,
            "limitations": ["not_bearer_access", "online_policy_and_pop_required"],
        }

    def freeze(self, certificate_fingerprint: str, *, reason_code: str) -> None:
        certificate = self._certificate(certificate_fingerprint)
        if certificate.status == AccessCertificateStatus.REVOKED.value:
            return
        certificate.status = "frozen"
        binding = self._binding(certificate_fingerprint, required=False)
        if binding:
            binding.status = "frozen"
        self.db.flush()
        if binding:
            self._audit_lifecycle("principal_certificate_frozen", binding, reason_code)

    def revoke(self, certificate_fingerprint: str, *, reason_code: str) -> None:
        certificate = self._certificate(certificate_fingerprint)
        binding = self._binding(certificate_fingerprint, required=False)
        if certificate.status == AccessCertificateStatus.REVOKED.value:
            return
        certificate.status = AccessCertificateStatus.REVOKED.value
        if binding:
            binding.status, binding.revoked_at = "revoked", self.clock()
        self.db.flush()
        if binding:
            self._audit_lifecycle("principal_certificate_revoked", binding, reason_code)

    def handle_principal_unlinked(self, principal_hash: str, *, proof_method: str) -> int:
        bindings = self.db.execute(
            select(AccessCertificatePrincipalBinding).where(
                AccessCertificatePrincipalBinding.principal_hash == principal_hash,
                AccessCertificatePrincipalBinding.status == "active",
            )
        ).scalars()
        count = 0
        for binding in bindings:
            if binding.proof_method == proof_method:
                self.freeze(binding.certificate_fingerprint, reason_code="principal_unlinked")
                self._audit_lifecycle("certificate_principal_unlinked", binding, "unlinked")
                count += 1
        return count

    @staticmethod
    def classify_legacy(
        certificate: AccessCertificate,
        binding: AccessCertificatePrincipalBinding | None,
    ) -> LegacyCertificateClass:
        if certificate.status == AccessCertificateStatus.REVOKED.value:
            return LegacyCertificateClass.REVOKED
        if binding:
            return LegacyCertificateClass.MIGRATED_PRINCIPAL_BOUND
        if certificate.device_key_fingerprint:
            return LegacyCertificateClass.LEGACY_DEVICE_BOUND
        return LegacyCertificateClass.LEGACY_UNBOUND

    def _validate_request(self, request: PrincipalCertificateIssueRequest) -> None:
        if request.principal_type not in SUPPORTED_PRINCIPAL_TYPES:
            raise PrincipalCertificateBridgeError("principal_not_found")
        for value in (
            request.principal_hash,
            request.device_key_fingerprint,
            request.session_hash,
            request.idempotency_key_hash,
        ):
            if not value.startswith(("sha256:", "hmac-sha256:", "hmac:")):
                raise PrincipalCertificateBridgeError("unsafe_principal_reference")
        if request.crypto_epoch not in self.supported_crypto_epochs:
            raise PrincipalCertificateBridgeError("crypto_epoch_unsupported")
        if not request.pop_request_verified:
            raise PrincipalCertificateBridgeError("session_invalid")
        if request.lockdown_state not in {None, "inactive"}:
            raise PrincipalCertificateBridgeError("lockdown_active")
        if request.recovery_state not in {None, "inactive", "complete"}:
            raise PrincipalCertificateBridgeError("recovery_locked")
        if request.requested_expires_at > self.clock() + timedelta(seconds=self.max_ttl_seconds):
            raise PrincipalCertificateBridgeError("certificate_expiry_too_long")
        profile = request.requested_assurance_profile
        if profile in HIGH_ASSURANCE_PROFILES and not request.step_up_satisfied:
            raise PrincipalCertificateBridgeError("step_up_required")
        if profile in HIGH_ASSURANCE_PROFILES and (
            request.proof_freshness_seconds is None or request.proof_freshness_seconds > 300
        ):
            raise PrincipalCertificateBridgeError("proof_too_old")
        if (
            profile
            in {
                CertificateAssuranceProfile.BUSINESS,
                CertificateAssuranceProfile.ENTERPRISE,
                CertificateAssuranceProfile.SOVEREIGN,
            }
            and not request.quorum_satisfied
        ):
            raise PrincipalCertificateBridgeError("quorum_required")
        if (
            request.delegation_requested or request.export_requested
        ) and not request.human_intent_verified:
            raise PrincipalCertificateBridgeError("step_up_required")
        if request.offline_pack_requested and profile in {
            CertificateAssuranceProfile.COMPATIBILITY,
            CertificateAssuranceProfile.STANDARD,
        }:
            raise PrincipalCertificateBridgeError("proof_too_weak")
        if request.proof_method == "legacy_message_signature":
            if profile is not CertificateAssuranceProfile.COMPATIBILITY:
                raise PrincipalCertificateBridgeError("proof_too_weak")
            if request.delegation_requested or request.offline_pack_requested:
                raise PrincipalCertificateBridgeError("proof_too_weak")
        if request.principal_type == "lightning_wallet_principal" and (
            request.requested_scopes & TREASURY_SCOPES
        ):
            raise PrincipalCertificateBridgeError("proof_too_weak")
        if (
            request.principal_type == "lightning_wallet_principal"
            and not request.auth_domain_verified
        ):
            raise PrincipalCertificateBridgeError("proof_too_weak")
        if (
            request.principal_type in {"business_owner_principal", "enterprise_principal"}
            and not request.business_role
        ):
            raise PrincipalCertificateBridgeError("policy_denied")

    def _principal(self, request: PrincipalCertificateIssueRequest) -> WalletPrincipal:
        principal = self.db.execute(
            select(WalletPrincipal)
            .where(WalletPrincipal.principal_hash == request.principal_hash)
            .with_for_update()
        ).scalar_one_or_none()
        if principal is None or principal.status != "active":
            raise PrincipalCertificateBridgeError("principal_inactive")
        if principal.revoked_at:
            raise PrincipalCertificateBridgeError("principal_revoked")
        if (
            request.principal_type
            in {
                "bitcoin_wallet_principal",
                "lightning_wallet_principal",
            }
            and principal.principal_type != request.principal_type
        ):
            raise PrincipalCertificateBridgeError("principal_inactive")
        return principal

    def _device(self, request: PrincipalCertificateIssueRequest) -> WalletDevice:
        device = self.db.execute(
            select(WalletDevice)
            .where(
                WalletDevice.principal_hash == request.principal_hash,
                WalletDevice.device_key_fingerprint == request.device_key_fingerprint,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if device is None or device.status != "active" or device.revoked_at:
            raise PrincipalCertificateBridgeError("device_binding_required")
        if (device.risk_score or 0) > 70:
            raise PrincipalCertificateBridgeError("device_binding_required")
        if (
            request.requested_assurance_profile in HIGH_ASSURANCE_PROFILES
            and device.device_class == "browser_extension"
        ):
            raise PrincipalCertificateBridgeError("device_binding_required")
        return device

    def _session(self, request: PrincipalCertificateIssueRequest) -> WalletSession:
        session = self.db.execute(
            select(WalletSession)
            .where(WalletSession.session_hash == request.session_hash)
            .with_for_update()
        ).scalar_one_or_none()
        if (
            session is None
            or session.principal_hash != request.principal_hash
            or session.device_key_fingerprint != request.device_key_fingerprint
            or session.status != "active"
            or _utc(session.expires_at) <= self.clock()
        ):
            raise PrincipalCertificateBridgeError("session_invalid")
        return session

    def _entitlement(self, request: PrincipalCertificateIssueRequest) -> SubscriptionEntitlement:
        entitlement = self.db.execute(
            select(SubscriptionEntitlement)
            .where(SubscriptionEntitlement.id == request.entitlement_id)
            .with_for_update()
        ).scalar_one_or_none()
        principal = (entitlement.metadata_json or {}).get("principal_hash") if entitlement else None
        if entitlement is None or principal != request.principal_hash:
            raise PrincipalCertificateBridgeError("entitlement_required")
        if (
            entitlement.status != SubscriptionEntitlementStatus.ACTIVE.value
            or entitlement.revoked_at
            or _utc(entitlement.valid_until) <= self.clock()
        ):
            raise PrincipalCertificateBridgeError("entitlement_expired")
        return entitlement

    def _check_revocations(
        self,
        request: PrincipalCertificateIssueRequest,
        principal: WalletPrincipal,
        device: WalletDevice,
        session: WalletSession,
        entitlement: SubscriptionEntitlement,
    ) -> None:
        status = self.revocations.check_certificate_bridge_targets(
            principal=principal.principal_hash,
            wallet_proof=sha256_prefixed(f"{request.principal_hash}:{request.proof_method}"),
            wallet_device=device.device_key_fingerprint,
            wallet_session=session.session_hash,
            subscription_entitlement=_entitlement_fingerprint(entitlement),
            issuer_key=self.issuer.issuer_key_id,
        )
        if any(bool(value) for value in status.values()):
            raise PrincipalCertificateBridgeError("principal_revoked")

    def _idempotent_result(
        self, request: PrincipalCertificateIssueRequest
    ) -> PrincipalCertificateResult | None:
        bindings = self.db.execute(select(AccessCertificatePrincipalBinding)).scalars()
        binding = next(
            (
                item
                for item in bindings
                if (item.metadata_json or {}).get("idempotency_key_hash")
                == request.idempotency_key_hash
                and item.status == "active"
            ),
            None,
        )
        if binding is None:
            return None
        if (
            binding.principal_hash != request.principal_hash
            or binding.device_key_fingerprint != request.device_key_fingerprint
            or binding.assurance_profile != request.requested_assurance_profile.value
        ):
            raise PrincipalCertificateBridgeError("idempotency_conflict")
        certificate = self._certificate(binding.certificate_fingerprint)
        payload = dict((binding.metadata_json or {}).get("certificate_payload", {}))
        return PrincipalCertificateResult(
            certificate.certificate_fingerprint,
            binding.principal_binding_hash,
            binding.principal_type,
            CertificateAssuranceProfile(binding.assurance_profile),
            tuple(_strings(certificate.scopes_json)),
            tuple((binding.metadata_json or {}).get("effective_metric_groups", [])),
            _utc(certificate.expires_at),
            payload,
        )

    def _build_export(
        self,
        binding: AccessCertificatePrincipalBinding,
        certificate_payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.export_enabled:
            raise PrincipalCertificateBridgeError("certificate_export_disabled")
        payload = {
            "type": "bastion_access_pass_export",
            "version": 2,
            "certificate": certificate_payload,
            "principal_binding": {
                "principal_type": binding.principal_type,
                "principal_binding_hash": binding.principal_binding_hash,
            },
            "device_binding_reference": {"device_key_fingerprint": binding.device_key_fingerprint},
            "entitlement_reference": {"entitlement_fingerprint": binding.entitlement_fingerprint},
            "exported_at": _iso(self.clock()),
            "export_policy": {
                "bearer_access": False,
                "device_proof_required": True,
                "pop_session_required": True,
                "online_revocation_check_required": True,
            },
        }
        payload["export_integrity_hash"] = sha256_prefixed(canonical_json(payload))
        return payload

    def _audit_request(
        self,
        request: PrincipalCertificateIssueRequest,
        decision: PrincipalCertificatePolicyDecision,
    ) -> None:
        self.audit.record_event(
            event_type="principal_certificate_requested",
            actor_hash=request.principal_hash,
            object_hash=request.device_key_fingerprint,
            metadata={
                "principal_type": request.principal_type,
                "proof_method": request.proof_method,
                "verification_strength": request.verification_strength,
                "policy_hash": decision.policy_hash,
                "decision": decision.decision,
                "reason_code": decision.reason_code,
            },
        )
        self.audit.record_event(
            event_type=(
                "principal_certificate_policy_allowed"
                if decision.decision == POLICY_DECISION_ALLOW
                else "principal_certificate_policy_denied"
            ),
            actor_hash=request.principal_hash,
            object_hash=request.device_key_fingerprint,
            metadata={
                "principal_type": request.principal_type,
                "policy_hash": decision.policy_hash,
                "decision": decision.decision,
                "reason_code": decision.reason_code,
            },
        )

    def _audit_lifecycle(
        self, event_type: str, binding: AccessCertificatePrincipalBinding, reason_code: str
    ) -> None:
        self.audit.record_event(
            event_type=event_type,
            actor_hash=binding.principal_hash,
            object_hash=binding.certificate_fingerprint,
            metadata={
                "principal_type": binding.principal_type,
                "principal_binding_hash": binding.principal_binding_hash,
                "proof_method": binding.proof_method,
                "verification_strength": binding.verification_strength,
                "device_key_fingerprint": binding.device_key_fingerprint,
                "entitlement_fingerprint": binding.entitlement_fingerprint,
                "assurance_profile": binding.assurance_profile,
                "policy_epoch": binding.policy_epoch,
                "crypto_epoch": binding.crypto_epoch,
                "reason_code": reason_code,
            },
        )

    def _metric(
        self, request: PrincipalCertificateIssueRequest, decision: str, reason: str
    ) -> None:
        if self.metric_emitter:
            try:
                name = (
                    "principal_certificate_issued_total"
                    if decision == "allow"
                    else "principal_certificate_denied_total"
                )
                self.metric_emitter(
                    name,
                    {
                        "principal_type": request.principal_type,
                        "assurance_profile": request.requested_assurance_profile.value,
                        "plan": "unknown",
                        "decision": decision,
                        "reason_code": reason,
                        "environment": "unknown",
                    },
                )
            except Exception:
                pass

    def _certificate(self, fingerprint: str) -> AccessCertificate:
        certificate = self.db.execute(
            select(AccessCertificate).where(
                AccessCertificate.certificate_fingerprint == fingerprint
            )
        ).scalar_one_or_none()
        if certificate is None:
            raise PrincipalCertificateBridgeError("certificate_not_found")
        return certificate

    def _binding(
        self, fingerprint: str, *, required: bool = True
    ) -> AccessCertificatePrincipalBinding | None:
        binding = self.db.execute(
            select(AccessCertificatePrincipalBinding).where(
                AccessCertificatePrincipalBinding.certificate_fingerprint == fingerprint
            )
        ).scalar_one_or_none()
        if binding is None and required:
            raise PrincipalCertificateBridgeError("certificate_rotation_required")
        return binding


def _entitlement_fingerprint(entitlement: SubscriptionEntitlement) -> str:
    return sha256_prefixed(
        canonical_json(
            {
                "id": entitlement.id,
                "plan": entitlement.plan_code,
                "valid_until": _iso(entitlement.valid_until),
                "issuer_key_id": entitlement.issuer_key_id,
                "crypto_epoch": entitlement.crypto_epoch,
            }
        )
    )


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


__all__ = [
    "AccessPolicyEngineCertificatePolicy",
    "CertificateAssuranceProfile",
    "LegacyCertificateClass",
    "PrincipalAccessCertificateBridge",
    "PrincipalCertificateBridgeError",
    "PrincipalCertificateIssueRequest",
    "PrincipalCertificatePolicyDecision",
    "PrincipalCertificateResult",
]
