"""LNURL-auth verified-proof to PoP session bridge.

This service coordinates existing LNURL-auth callback verification, Lightning
Principal, Device Binding, entitlement, Policy Engine, and PoP session services.
It does not verify ECDSA signatures, implement LNURL routes, issue entitlements,
issue Access Certificates, or treat LNURL-auth alone as unrestricted access.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.lnurl.principals import LightningPrincipalStatus
from app.domain.wallet_auth.devices import WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.principals import WalletPrincipalActorType
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.lnurl.auth_callback_verifier import LNURLAuthVerificationResult, VerifiedLNURLAuthProof
from app.services.lnurl.principal_service import (
    LightningPrincipalAuthenticationContext,
    LightningPrincipalService,
)
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input
from app.services.wallet_auth.principal_types import PrincipalType
from app.services.wallet_auth.session_service import EntitlementSnapshot, PolicyDecision, VerifiedWalletAuthenticationContext, WalletSessionCreationResult


class LNURLAuthSessionBridgeStatus(StrEnum):
    SESSION_CREATED = "session_created"
    STEP_UP_CREATED = "step_up_created"
    LINKED = "linked"
    DENIED = "denied"


class LNURLAuthSessionBridgeReason(StrEnum):
    INVALID_VERIFIED_CALLBACK = "invalid_verified_callback"
    CALLBACK_NOT_CONSUMED = "callback_not_consumed"
    REPLAY_DETECTED = "replay_detected"
    CHALLENGE_EXPIRED = "challenge_expired"
    ACTION_MISMATCH = "action_mismatch"
    DOMAIN_MISMATCH = "domain_mismatch"
    PRINCIPAL_NOT_FOUND = "principal_not_found"
    PRINCIPAL_SUSPENDED = "principal_suspended"
    PRINCIPAL_REVOKED = "principal_revoked"
    PRINCIPAL_RECOVERY_LOCKED = "principal_recovery_locked"
    DEVICE_PROOF_INVALID = "device_proof_invalid"
    DEVICE_REVOKED = "device_revoked"
    ENTITLEMENT_EXPIRED = "entitlement_expired"
    SUBSCRIPTION_UPGRADE_REQUIRED = "subscription_upgrade_required"
    POLICY_DENIED = "policy_denied"
    STEP_UP_REQUIRED = "step_up_required"
    ACCESS_CERTIFICATE_REQUIRED = "access_certificate_required"
    SESSION_CREATION_FAILED = "session_creation_failed"
    WILDCARD_SCOPE_REJECTED = "wildcard_scope_rejected"


class LNURLAuthSessionBridgeError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeError): ...
class LNURLAuthSessionPrincipalError(LNURLAuthSessionBridgeError): ...
class LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeError): ...
class LNURLAuthSessionEntitlementError(LNURLAuthSessionBridgeError): ...
class LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeError): ...
class LNURLAuthSessionCreationError(LNURLAuthSessionBridgeError): ...


@dataclass(frozen=True, slots=True)
class VerifiedLNURLAuthSessionInput:
    verified: bool
    consumed: bool
    replay_status: str
    action: LNURLAuthAction
    auth_domain: str
    k1_hash: str
    linking_key_hash: str
    proof_type: str
    verification_strength: WalletVerificationStrength
    challenge_id: str
    verified_at: datetime
    callback_fingerprint: str
    policy_intent_hash: str
    device_key_fingerprint: str | None = None
    proof: VerifiedLNURLAuthProof | None = None
    result: LNURLAuthVerificationResult | None = None
    limitations: tuple[str, ...] = ()

    @classmethod
    def from_callback_result(
        cls,
        result: LNURLAuthVerificationResult,
        *,
        consumed: bool,
        replay_status: str,
        k1_hash: str,
        callback_fingerprint: str | None = None,
    ) -> VerifiedLNURLAuthSessionInput:
        if result.proof is None or result.lnurl_action is None or result.lnurl_key_hash is None or result.verification_strength is None or result.verified_at is None:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.INVALID_VERIFIED_CALLBACK.value)
        return cls(
            verified=result.verified,
            consumed=consumed,
            replay_status=replay_status,
            action=result.lnurl_action,
            auth_domain=result.auth_domain or result.proof.auth_domain,
            k1_hash=k1_hash,
            linking_key_hash=result.lnurl_key_hash,
            proof_type="lnurl_auth",
            verification_strength=result.verification_strength,
            challenge_id=result.challenge_id or result.proof.challenge_id,
            verified_at=result.verified_at,
            callback_fingerprint=callback_fingerprint or sha256_prefixed(result.challenge_id or result.proof.challenge_id),
            policy_intent_hash=result.policy_intent_hash or result.proof.policy_intent_hash,
            device_key_fingerprint=result.device_key_fingerprint,
            proof=result.proof,
            result=result,
            limitations=tuple(result.limitations),
        )


@dataclass(frozen=True, slots=True)
class LNURLAuthSessionBridgeRequest:
    verified_callback_result: VerifiedLNURLAuthSessionInput
    action: LNURLAuthAction
    auth_domain: str
    challenge_id: str
    k1_hash: str
    linking_key_hash: str
    device_public_key: str = field(repr=False)
    device_key_fingerprint: str
    device_binding_signature: str = field(repr=False)
    device_class: WalletDeviceClass
    requested_scopes: tuple[str, ...] = ()
    requested_metric_groups: tuple[str, ...] = ()
    client_origin: str = ""
    client_ip_hash: str | None = None
    user_agent_hash: str | None = None
    existing_session_context: Mapping[str, object] | None = None
    principal_hint: str | None = None
    pending_intent_hash: str | None = None
    requested_session_ttl_seconds: int | None = None
    normalized_linking_public_key: str | None = field(default=None, repr=False)
    session_public_key: str | bytes | None = field(default=None, repr=False)
    session_public_key_fingerprint: str | None = None
    request_context: Mapping[str, object] = field(default_factory=dict, repr=False)


@dataclass(frozen=True, slots=True)
class DeviceBindingBridgeResult:
    device_binding_id: int
    device_key_fingerprint: str
    status: WalletDeviceStatus
    device_class: WalletDeviceClass
    risk_score: int
    risk_level: str
    created: bool


@dataclass(frozen=True, slots=True)
class StepUpAuthorization:
    step_up_proof_id: str
    intent_hash: str
    approved_action: str
    approved_scopes: tuple[str, ...]
    valid_until: datetime
    principal_hash: str
    device_key_fingerprint: str
    policy_decision_hash: str


@dataclass(frozen=True, slots=True)
class LNURLAuthSessionBridgeResult:
    status: LNURLAuthSessionBridgeStatus
    principal_hash: str
    principal_type: str
    device_binding_status: str
    session_token: str | None
    session_expires_at: datetime | None
    approved_scopes: tuple[str, ...]
    denied_scopes: tuple[str, ...]
    plan: str
    entitlement_status: str
    verification_strength: WalletVerificationStrength
    requires_step_up: bool
    step_up_reason: str | None
    policy_decision: str
    audit_event_hash: str | None
    access_certificate_required: bool
    limitations: tuple[str, ...]
    next_action: str | None = None
    step_up: StepUpAuthorization | None = None


class DeviceBindingBridge(Protocol):
    async def verify_or_bind_device(self, *, principal: LightningPrincipalAuthenticationContext, request: LNURLAuthSessionBridgeRequest, proof: VerifiedLNURLAuthSessionInput, allow_new_device: bool) -> DeviceBindingBridgeResult: ...


class EntitlementBridge(Protocol):
    async def get_entitlement_for_principal(self, principal_hash: str) -> EntitlementSnapshot: ...


class PolicyEngineBridge(Protocol):
    async def decide_lnurl_auth_session(self, context: Mapping[str, object]) -> PolicyDecision: ...


class PoPSessionBridge(Protocol):
    async def create_session(self, *, auth_context: VerifiedWalletAuthenticationContext, session_public_key: str | bytes, requested_ttl_seconds: int | None = None) -> WalletSessionCreationResult: ...


class RevocationBridge(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


AuditEmitter = Callable[[str, Mapping[str, object]], None]
MetricsEmitter = Callable[[str, Mapping[str, str]], None]
Clock = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class LNURLAuthSessionBridgeConfig:
    default_register_ttl_seconds: int = 600
    default_login_ttl_seconds: int = 900
    default_step_up_ttl_seconds: int = 300
    max_business_ttl_seconds: int = 300
    proof_freshness_seconds: int = 300
    allow_restricted_session_on_upgrade_required: bool = True


class LNURLAuthSessionBridge:
    def __init__(
        self,
        *,
        principal_service: LightningPrincipalService,
        device_binding: DeviceBindingBridge,
        entitlement_service: EntitlementBridge,
        policy_engine: PolicyEngineBridge,
        pop_session_service: PoPSessionBridge,
        revocation_registry: RevocationBridge | None = None,
        audit_emitter: AuditEmitter | None = None,
        metrics_emitter: MetricsEmitter | None = None,
        clock: Clock | None = None,
        config: LNURLAuthSessionBridgeConfig = LNURLAuthSessionBridgeConfig(),
    ) -> None:
        self.principal_service = principal_service
        self.device_binding = device_binding
        self.entitlement_service = entitlement_service
        self.policy_engine = policy_engine
        self.pop_session_service = pop_session_service
        self.revocation_registry = revocation_registry
        self.audit_emitter = audit_emitter
        self.metrics_emitter = metrics_emitter
        self.clock = clock or (lambda: datetime.now(UTC))
        self.config = config

    async def create_session(self, request: LNURLAuthSessionBridgeRequest) -> LNURLAuthSessionBridgeResult:
        self._validate_request(request)
        proof = request.verified_callback_result
        self._emit("lnurl_session_bridge_started", request=request, reason_code="started")
        try:
            principal_context = await self._resolve_principal(request)
            self._check_revocations(principal_context=principal_context, request=request)
            allow_new_device = request.action in {LNURLAuthAction.REGISTER, LNURLAuthAction.LOGIN}
            device = await self.device_binding.verify_or_bind_device(principal=principal_context, request=request, proof=proof, allow_new_device=allow_new_device)
            if device.status is WalletDeviceStatus.REVOKED:
                raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_REVOKED.value)
            self._emit("lnurl_device_bound" if device.created else "lnurl_principal_resolved", request=request, principal_hash=principal_context.principal_hash, device_fingerprint=device.device_key_fingerprint, reason_code="device_ok")
            entitlement = await self.entitlement_service.get_entitlement_for_principal(principal_context.principal_hash)
            policy_input = self._policy_input(request=request, principal=principal_context, device=device, entitlement=entitlement)
            decision = await self.policy_engine.decide_lnurl_auth_session(policy_input)
            if decision.decision == "deny" or (not decision.allowed and decision.decision not in {"step_up_required", "upgrade_required", "access_certificate_required"}):
                self._emit("lnurl_session_policy_denied", request=request, principal_hash=principal_context.principal_hash, policy_decision_hash=decision.decision_hash, reason_code=decision.reason_code)
                raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.POLICY_DENIED.value)
            if decision.decision == "step_up_required":
                self._emit("lnurl_session_policy_denied", request=request, principal_hash=principal_context.principal_hash, policy_decision_hash=decision.decision_hash, reason_code=LNURLAuthSessionBridgeReason.STEP_UP_REQUIRED.value)
                raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.STEP_UP_REQUIRED.value)
            if request.action is LNURLAuthAction.AUTH:
                return self._create_step_up_result(request=request, principal=principal_context, device=device, entitlement=entitlement, decision=decision)
            if request.action is LNURLAuthAction.LINK:
                return self._create_link_result(request=request, principal=principal_context, device=device, entitlement=entitlement, decision=decision)
            if decision.decision == "access_certificate_required":
                return self._restricted_result(request=request, principal=principal_context, device=device, entitlement=entitlement, decision=decision, reason=LNURLAuthSessionBridgeReason.ACCESS_CERTIFICATE_REQUIRED.value, next_action="issue_access_certificate")
            if decision.decision == "upgrade_required" and not self.config.allow_restricted_session_on_upgrade_required:
                raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.SUBSCRIPTION_UPGRADE_REQUIRED.value)
            session = await self._create_pop_session(request=request, principal=principal_context, device=device, entitlement=entitlement, decision=decision)
            audit_hash = self._emit("lnurl_session_created", request=request, principal_hash=principal_context.principal_hash, device_fingerprint=device.device_key_fingerprint, policy_decision_hash=decision.decision_hash, session_fingerprint=sha256_prefixed(session.session_token), reason_code="session_created")
            self._metric("lnurl_auth_session_created_total", action=request.action.value, result="created", decision=decision.decision, strength=proof.verification_strength.value)
            return LNURLAuthSessionBridgeResult(
                status=LNURLAuthSessionBridgeStatus.SESSION_CREATED,
                principal_hash=principal_context.principal_hash,
                principal_type=principal_context.principal_type,
                device_binding_status=device.status.value,
                session_token=session.session_token,
                session_expires_at=session.expires_at,
                approved_scopes=tuple(session.effective_scopes),
                denied_scopes=tuple(sorted(set(request.requested_scopes) - set(session.effective_scopes))),
                plan=entitlement.effective_plan,
                entitlement_status="active" if entitlement.active else "inactive",
                verification_strength=proof.verification_strength,
                requires_step_up=False,
                step_up_reason=None,
                policy_decision=decision.decision,
                audit_event_hash=audit_hash,
                access_certificate_required=False,
                limitations=proof.limitations,
            )
        except LNURLAuthSessionBridgeError as exc:
            self._emit("lnurl_session_bridge_failed", request=request, reason_code=exc.reason_code)
            self._metric("lnurl_auth_session_bridge_error_total", action=request.action.value, result="error", decision=exc.reason_code, strength=request.verified_callback_result.verification_strength.value)
            raise

    async def _resolve_principal(self, request: LNURLAuthSessionBridgeRequest) -> LightningPrincipalAuthenticationContext:
        proof = request.verified_callback_result
        existing = self.principal_service.find_by_principal_hash(request.principal_hint) if request.principal_hint else None
        if existing is None and request.normalized_linking_public_key is not None:
            existing = self.principal_service.find_by_lnurl_key(normalized_linking_public_key=request.normalized_linking_public_key, auth_domain=proof.auth_domain)
        if request.action is LNURLAuthAction.REGISTER:
            if existing is None:
                if proof.proof is None or request.normalized_linking_public_key is None:
                    raise LNURLAuthSessionPrincipalError(LNURLAuthSessionBridgeReason.PRINCIPAL_NOT_FOUND.value)
                created = self.principal_service.create_from_verified_lnurl_auth(
                    proof=proof.proof,
                    normalized_linking_public_key=request.normalized_linking_public_key,
                    proof_fingerprint=proof.callback_fingerprint,
                    policy_hash=proof.policy_intent_hash,
                    request_context=request.request_context,
                )
                self._emit("lnurl_principal_created", request=request, principal_hash=created.principal.principal_hash, reason_code="created")
                return self.principal_service.authentication_context(created.principal, revocation_checked=True)
            return self.principal_service.find_active_principal(existing.principal_hash, device_key_fingerprint=request.device_key_fingerprint)
        if existing is None:
            raise LNURLAuthSessionPrincipalError(LNURLAuthSessionBridgeReason.PRINCIPAL_NOT_FOUND.value)
        context = self.principal_service.find_active_principal(existing.principal_hash, device_key_fingerprint=request.device_key_fingerprint)
        if context.status is LightningPrincipalStatus.RECOVERY_LOCKED:
            if request.action is not LNURLAuthAction.LOGIN:
                raise LNURLAuthSessionPrincipalError(LNURLAuthSessionBridgeReason.PRINCIPAL_RECOVERY_LOCKED.value)
        self._emit("lnurl_principal_resolved", request=request, principal_hash=context.principal_hash, reason_code="resolved")
        return context

    async def _create_pop_session(
        self,
        *,
        request: LNURLAuthSessionBridgeRequest,
        principal: LightningPrincipalAuthenticationContext,
        device: DeviceBindingBridgeResult,
        entitlement: EntitlementSnapshot,
        decision: PolicyDecision,
    ) -> WalletSessionCreationResult:
        if request.session_public_key is None or request.session_public_key_fingerprint is None:
            raise LNURLAuthSessionCreationError(LNURLAuthSessionBridgeReason.SESSION_CREATION_FAILED.value)
        auth_context = self._wallet_session_context(request=request, principal=principal, device=device, entitlement=entitlement, decision=decision)
        return await self.pop_session_service.create_session(auth_context=auth_context, session_public_key=request.session_public_key, requested_ttl_seconds=self._ttl_for(request, entitlement))

    def _wallet_session_context(
        self,
        *,
        request: LNURLAuthSessionBridgeRequest,
        principal: LightningPrincipalAuthenticationContext,
        device: DeviceBindingBridgeResult,
        entitlement: EntitlementSnapshot,
        decision: PolicyDecision,
    ) -> VerifiedWalletAuthenticationContext:
        proof = request.verified_callback_result
        approved_scopes = self._approved_scopes(request.requested_scopes, entitlement.allowed_scopes)
        return VerifiedWalletAuthenticationContext(
            principal_hash=principal.principal_hash,
            principal_type=PrincipalType.LIGHTNING_WALLET_PRINCIPAL,
            principal_status=_wallet_status(principal.status),
            proof_fingerprint=proof.callback_fingerprint,
            proof_type=WalletProofType.LNURL_AUTH,
            verification_strength=proof.verification_strength,
            proof_verified_at=proof.verified_at,
            challenge_id=proof.challenge_id,
            challenge_hash=proof.k1_hash,
            challenge_action=proof.action.value,
            challenge_origin=request.client_origin,
            challenge_used=True,
            device_binding_id=device.device_binding_id,
            device_key_fingerprint=device.device_key_fingerprint,
            device_status=device.status,
            device_risk_score=device.risk_score,
            requested_scopes=approved_scopes,
            auth_method="lnurl_auth",
            policy_hash=decision.decision_hash,
            policy_epoch=1,
            crypto_epoch=1,
            origin=request.client_origin,
            expected_session_public_key_fingerprint=request.session_public_key_fingerprint or "sha256:missing",
            expected_device_key_fingerprint=request.device_key_fingerprint,
            entitlement_required=True,
            recovery_only_requested=principal.status is LightningPrincipalStatus.RECOVERY_LOCKED,
            proof_expires_at=proof.verified_at + timedelta(seconds=self.config.proof_freshness_seconds),
        )

    def _create_step_up_result(
        self,
        *,
        request: LNURLAuthSessionBridgeRequest,
        principal: LightningPrincipalAuthenticationContext,
        device: DeviceBindingBridgeResult,
        entitlement: EntitlementSnapshot,
        decision: PolicyDecision,
    ) -> LNURLAuthSessionBridgeResult:
        if not request.pending_intent_hash:
            raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.STEP_UP_REQUIRED.value)
        proof = request.verified_callback_result
        approved = self._approved_scopes(request.requested_scopes, entitlement.allowed_scopes)
        step_up = StepUpAuthorization(
            step_up_proof_id=sha256_prefixed(canonical_json({"challenge_id": proof.challenge_id, "intent_hash": request.pending_intent_hash, "principal_hash": principal.principal_hash})),
            intent_hash=request.pending_intent_hash,
            approved_action=proof.action.value,
            approved_scopes=approved,
            valid_until=min(proof.verified_at + timedelta(seconds=self.config.default_step_up_ttl_seconds), self.clock() + timedelta(seconds=self.config.default_step_up_ttl_seconds)),
            principal_hash=principal.principal_hash,
            device_key_fingerprint=device.device_key_fingerprint,
            policy_decision_hash=decision.decision_hash,
        )
        audit_hash = self._emit("lnurl_step_up_created", request=request, principal_hash=principal.principal_hash, device_fingerprint=device.device_key_fingerprint, policy_decision_hash=decision.decision_hash, reason_code="step_up_created")
        return LNURLAuthSessionBridgeResult(
            status=LNURLAuthSessionBridgeStatus.STEP_UP_CREATED,
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            device_binding_status=device.status.value,
            session_token=None,
            session_expires_at=step_up.valid_until,
            approved_scopes=approved,
            denied_scopes=tuple(sorted(set(request.requested_scopes) - set(approved))),
            plan=entitlement.effective_plan,
            entitlement_status="active" if entitlement.active else "inactive",
            verification_strength=proof.verification_strength,
            requires_step_up=False,
            step_up_reason=None,
            policy_decision=decision.decision,
            audit_event_hash=audit_hash,
            access_certificate_required=False,
            limitations=proof.limitations + ("step_up_bound_to_pending_intent",),
            step_up=step_up,
        )

    def _create_link_result(
        self, *, request: LNURLAuthSessionBridgeRequest, principal: LightningPrincipalAuthenticationContext, device: DeviceBindingBridgeResult, entitlement: EntitlementSnapshot, decision: PolicyDecision) -> LNURLAuthSessionBridgeResult:
        if request.existing_session_context is None or not request.pending_intent_hash:
            raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.POLICY_DENIED.value)
        audit_hash = self._emit("lnurl_principal_linked", request=request, principal_hash=principal.principal_hash, device_fingerprint=device.device_key_fingerprint, policy_decision_hash=decision.decision_hash, reason_code="linked")
        return LNURLAuthSessionBridgeResult(
            status=LNURLAuthSessionBridgeStatus.LINKED,
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            device_binding_status=device.status.value,
            session_token=None,
            session_expires_at=None,
            approved_scopes=(),
            denied_scopes=request.requested_scopes,
            plan=entitlement.effective_plan,
            entitlement_status="active" if entitlement.active else "inactive",
            verification_strength=request.verified_callback_result.verification_strength,
            requires_step_up=False,
            step_up_reason=None,
            policy_decision=decision.decision,
            audit_event_hash=audit_hash,
            access_certificate_required=False,
            limitations=("principal_link_requires_existing_pop_session", "no_automatic_merge"),
        )

    def _restricted_result(self, *, request: LNURLAuthSessionBridgeRequest, principal: LightningPrincipalAuthenticationContext, device: DeviceBindingBridgeResult, entitlement: EntitlementSnapshot, decision: PolicyDecision, reason: str, next_action: str | None) -> LNURLAuthSessionBridgeResult:
        audit_hash = self._emit("lnurl_session_policy_denied", request=request, principal_hash=principal.principal_hash, device_fingerprint=device.device_key_fingerprint, policy_decision_hash=decision.decision_hash, reason_code=reason)
        return LNURLAuthSessionBridgeResult(
            status=LNURLAuthSessionBridgeStatus.DENIED,
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            device_binding_status=device.status.value,
            session_token=None,
            session_expires_at=None,
            approved_scopes=(),
            denied_scopes=request.requested_scopes,
            plan=entitlement.effective_plan,
            entitlement_status="active" if entitlement.active else "inactive",
            verification_strength=request.verified_callback_result.verification_strength,
            requires_step_up=reason == LNURLAuthSessionBridgeReason.STEP_UP_REQUIRED.value,
            step_up_reason=reason,
            policy_decision=decision.decision,
            audit_event_hash=audit_hash,
            access_certificate_required=reason == LNURLAuthSessionBridgeReason.ACCESS_CERTIFICATE_REQUIRED.value,
            limitations=(reason,),
            next_action=next_action,
        )

    def _validate_request(self, request: LNURLAuthSessionBridgeRequest) -> None:
        proof = request.verified_callback_result
        for key, value in request.request_context.items():
            reject_forbidden_wallet_secret_input(str(key), "bridge_context_key")
            if isinstance(value, str):
                reject_forbidden_wallet_secret_input(value, str(key))
        if not proof.verified:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.INVALID_VERIFIED_CALLBACK.value)
        if not proof.consumed:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.CALLBACK_NOT_CONSUMED.value)
        if proof.replay_status not in {"consumed", "fresh", "ok"}:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.REPLAY_DETECTED.value)
        if proof.action is not request.action:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.ACTION_MISMATCH.value)
        if proof.auth_domain != request.auth_domain:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.DOMAIN_MISMATCH.value)
        if proof.challenge_id != request.challenge_id or proof.k1_hash != request.k1_hash or proof.linking_key_hash != request.linking_key_hash:
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.INVALID_VERIFIED_CALLBACK.value)
        if proof.proof_type != "lnurl_auth":
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.INVALID_VERIFIED_CALLBACK.value)
        if proof.verified_at.tzinfo is None or self.clock() - proof.verified_at > timedelta(seconds=self.config.proof_freshness_seconds):
            raise LNURLAuthSessionInvalidCallbackError(LNURLAuthSessionBridgeReason.CHALLENGE_EXPIRED.value)
        if not request.device_public_key or not request.device_key_fingerprint or not request.device_binding_signature:
            raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_PROOF_INVALID.value)
        if not request.device_key_fingerprint.startswith("sha256:"):
            raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_PROOF_INVALID.value)
        if any(scope == "*" or scope.endswith(":all") or "*" in scope for scope in request.requested_scopes):
            raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.WILDCARD_SCOPE_REJECTED.value)
        if request.action is LNURLAuthAction.AUTH and not request.pending_intent_hash:
            raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.STEP_UP_REQUIRED.value)
        if request.action is LNURLAuthAction.LINK and request.existing_session_context is None:
            raise LNURLAuthSessionPolicyError(LNURLAuthSessionBridgeReason.POLICY_DENIED.value)

    def _policy_input(self, *, request: LNURLAuthSessionBridgeRequest, principal: LightningPrincipalAuthenticationContext, device: DeviceBindingBridgeResult, entitlement: EntitlementSnapshot) -> dict[str, object]:
        proof = request.verified_callback_result
        return {
            "actor_type": WalletPrincipalActorType.LIGHTNING_WALLET_PRINCIPAL.value,
            "auth_method": "lnurl_auth",
            "principal_hash": principal.principal_hash,
            "device_key_fingerprint": device.device_key_fingerprint,
            "device_class": device.device_class.value,
            "device_status": device.status.value,
            "verification_strength": proof.verification_strength.value,
            "wallet_proof_freshness_seconds": int((self.clock() - proof.verified_at).total_seconds()),
            "auth_domain": proof.auth_domain,
            "lnurl_action": proof.action.value,
            "requested_scopes": tuple(request.requested_scopes),
            "requested_metric_groups": tuple(request.requested_metric_groups),
            "subscription_plan": entitlement.effective_plan,
            "subscription_status": "active" if entitlement.active else "inactive",
            "requested_session_ttl_seconds": request.requested_session_ttl_seconds,
            "revocation_state": "checked",
            "recovery_state": principal.status.value,
            "pending_intent_hash": request.pending_intent_hash,
            "existing_session_context": dict(request.existing_session_context or {}),
            "client_origin": request.client_origin,
        }

    def _check_revocations(self, *, principal_context: LightningPrincipalAuthenticationContext, request: LNURLAuthSessionBridgeRequest) -> None:
        if self.revocation_registry is None:
            return
        proof = request.verified_callback_result
        checks = [
            ("lightning_wallet_principal", principal_context.principal_hash),
            ("lnurl_auth_key_hash", proof.linking_key_hash),
            ("wallet_device", request.device_key_fingerprint),
            ("auth_domain", sha256_prefixed(proof.auth_domain)),
        ]
        for target_type, target_hash in checks:
            if self.revocation_registry.is_revoked(target_type=target_type, target_hash=target_hash):
                raise LNURLAuthSessionPrincipalError(LNURLAuthSessionBridgeReason.PRINCIPAL_REVOKED.value)

    def _approved_scopes(self, requested: Sequence[str], allowed: Sequence[str]) -> tuple[str, ...]:
        if "*" in allowed:
            return tuple(sorted(set(requested)))
        return tuple(sorted(set(requested).intersection(set(allowed))))

    def _ttl_for(self, request: LNURLAuthSessionBridgeRequest, entitlement: EntitlementSnapshot) -> int:
        if request.action is LNURLAuthAction.REGISTER:
            base = self.config.default_register_ttl_seconds
        elif request.action is LNURLAuthAction.AUTH:
            base = self.config.default_step_up_ttl_seconds
        else:
            base = self.config.default_login_ttl_seconds
        if request.requested_session_ttl_seconds is not None:
            base = min(base, request.requested_session_ttl_seconds)
        if entitlement.expires_at is not None:
            base = min(base, max(1, int((entitlement.expires_at - self.clock()).total_seconds())))
        return max(1, base)

    def _emit(self, event: str, *, request: LNURLAuthSessionBridgeRequest, reason_code: str, principal_hash: str | None = None, device_fingerprint: str | None = None, policy_decision_hash: str | None = None, session_fingerprint: str | None = None) -> str:
        payload = {
            "principal_hash": principal_hash,
            "device_fingerprint": device_fingerprint,
            "callback_fingerprint": request.verified_callback_result.callback_fingerprint,
            "challenge_hash": request.k1_hash,
            "policy_decision_hash": policy_decision_hash,
            "session_fingerprint": session_fingerprint,
            "approved_scopes": tuple(scope for scope in request.requested_scopes if scope != "*"),
            "reason_code": reason_code,
            "action": request.action.value,
            "auth_domain_hash": sha256_prefixed(request.auth_domain),
            "timestamp": self.clock().isoformat(),
        }
        audit_hash = sha256_prefixed(canonical_json(payload))
        payload["audit_event_hash"] = audit_hash
        if self.audit_emitter:
            self.audit_emitter(event, payload)
        return audit_hash

    def _metric(self, name: str, *, action: str, result: str, decision: str, strength: str) -> None:
        if self.metrics_emitter:
            self.metrics_emitter(name, {"action": action, "result": result, "policy_decision": decision, "verification_strength": strength, "device_class": "known"})


def _wallet_status(status: LightningPrincipalStatus) -> Any:
    from app.domain.wallet_auth.principals import WalletPrincipalStatus

    if status is LightningPrincipalStatus.ACTIVE:
        return WalletPrincipalStatus.ACTIVE
    if status is LightningPrincipalStatus.SUSPENDED:
        return WalletPrincipalStatus.SUSPENDED
    if status is LightningPrincipalStatus.REVOKED:
        return WalletPrincipalStatus.REVOKED
    if status is LightningPrincipalStatus.RECOVERY_LOCKED:
        return WalletPrincipalStatus.RECOVERY_LOCKED
    return WalletPrincipalStatus.PENDING_VERIFICATION


__all__ = [
    "DeviceBindingBridgeResult",
    "LNURLAuthSessionBridge",
    "LNURLAuthSessionBridgeConfig",
    "LNURLAuthSessionBridgeError",
    "LNURLAuthSessionBridgeRequest",
    "LNURLAuthSessionBridgeResult",
    "LNURLAuthSessionBridgeStatus",
    "StepUpAuthorization",
    "VerifiedLNURLAuthSessionInput",
]
