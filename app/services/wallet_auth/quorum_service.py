"""Transactional coordinator for independent wallet/LNURL authority approvals."""

from __future__ import annotations

import hmac
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.wallet_auth import MultiWalletQuorum
from app.domain.wallet_auth.quorum import (
    QuorumDecision,
    QuorumEvaluation,
    QuorumFailureReason,
    QuorumParticipantSlot,
    QuorumParticipantType,
    QuorumPolicy,
    QuorumProofMethod,
    QuorumStatus,
    QuorumType,
    VerifiedQuorumApproval,
)
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import (
    hmac_sha256_prefixed,
    secure_nonce_hex,
)
from app.services.wallet_auth.recovery.models import RecoveryCapsule
from app.services.wallet_auth.step_up_policy import QuorumState
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine, POLICY_DECISION_ALLOW


class QuorumError(ValueError):
    """Safe, machine-readable quorum failure."""


class QuorumRevocationChecker(Protocol):
    def check_quorum_targets(self, **targets: str | None) -> Mapping[str, object]: ...


class QuorumPolicyAuthorizer(Protocol):
    def authorize_quorum(
        self,
        *,
        action: str,
        policy: QuorumPolicy,
        evaluation: QuorumEvaluation,
    ) -> tuple[bool, str]: ...


MetricEmitter = Callable[[str, dict[str, str]], None]


class AccessPolicyEngineQuorumAuthorizer:
    """Adapter that keeps the existing Access Policy Engine as final authority."""

    def __init__(
        self,
        engine: AccessPolicyEngine,
        context_factory: Callable[[str, QuorumPolicy, QuorumEvaluation], AccessPolicyContext],
    ) -> None:
        self.engine, self.context_factory = engine, context_factory

    def authorize_quorum(
        self,
        *,
        action: str,
        policy: QuorumPolicy,
        evaluation: QuorumEvaluation,
    ) -> tuple[bool, str]:
        context = self.context_factory(action, policy, evaluation)
        decision = self.engine.evaluate(context)
        return decision.decision == POLICY_DECISION_ALLOW, decision.reason_code


class WalletQuorumService:
    """Coordinates already-verified proofs; it does not implement cryptography."""

    def __init__(
        self,
        db: Session,
        *,
        server_pepper: str,
        policy_authorizer: QuorumPolicyAuthorizer,
        revocation_checker: QuorumRevocationChecker,
        audit_chain: AccessAuditChain | None = None,
        metric_emitter: MetricEmitter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not server_pepper:
            raise QuorumError("quorum_pepper_required")
        self.db, self.server_pepper = db, server_pepper
        self.policy_authorizer, self.revocations = policy_authorizer, revocation_checker
        self.audit = audit_chain or AccessAuditChain(db)
        self.metric_emitter = metric_emitter
        self.clock = clock or (lambda: datetime.now(UTC))

    def create(
        self,
        *,
        principal_hash: str,
        policy: QuorumPolicy,
        intent_hash: str,
        active_pop_session: bool,
        human_intent_verified: bool,
        recovery_capsule_hash: str | None = None,
        idempotency_key_hash: str | None = None,
    ) -> tuple[str, QuorumEvaluation]:
        if policy.require_active_pop_session and not active_pop_session:
            raise QuorumError(QuorumFailureReason.SESSION_INVALID.value)
        if policy.require_human_intent and not human_intent_verified:
            raise QuorumError("human_intent_required")
        if policy.require_recovery_capsule and not recovery_capsule_hash:
            raise QuorumError("recovery_capsule_required")
        if not intent_hash or not policy.action:
            raise QuorumError("quorum_intent_required")
        if idempotency_key_hash:
            existing = self._find_idempotent(idempotency_key_hash)
            if existing is not None:
                if (existing.metadata_json or {}).get("intent_hash") != intent_hash:
                    raise QuorumError("quorum_idempotency_conflict")
                return existing.quorum_hash, self._evaluate_row(existing)
        now = self.clock()
        quorum_hash = hmac_sha256_prefixed(
            self.server_pepper,
            f"quorum:{secure_nonce_hex(32)}:{policy.policy_hash}",
        )
        initial = QuorumEvaluation(
            QuorumStatus.PENDING,
            QuorumDecision.PENDING,
            "quorum_pending",
            policy.threshold,
            0,
            0,
            0,
            (),
            policy_hash=policy.policy_hash,
        )
        allowed, reason = self.policy_authorizer.authorize_quorum(
            action="quorum_create", policy=policy, evaluation=initial
        )
        if not allowed:
            raise QuorumError(reason or QuorumDecision.POLICY_DENIED.value)
        row = MultiWalletQuorum(
            principal_hash=principal_hash,
            quorum_hash=quorum_hash,
            quorum_type=policy.quorum_type.value,
            threshold_required=policy.threshold,
            participant_count=len(policy.participant_slots),
            participant_hashes_json=[],
            allowed_proof_types_json=sorted(item.value for item in policy.allowed_proof_methods),
            role_constraints_json={
                "required_roles": sorted(policy.required_roles),
                "slots": [slot.canonical_payload() for slot in policy.participant_slots],
            },
            status=QuorumStatus.PENDING.value,
            policy_hash=policy.policy_hash,
            created_at=now,
            updated_at=now,
            metadata_json={
                "policy": policy.canonical_payload(),
                "intent_hash": intent_hash,
                "action": policy.action,
                "expires_at": (now + timedelta(seconds=policy.expires_in_seconds)).isoformat(),
                "cooldown_until": None,
                "approvals": [],
                "recovery_capsule_hash": recovery_capsule_hash,
                "idempotency_key_hash": idempotency_key_hash,
                "policy_epoch": policy.policy_epoch,
                "crypto_epoch": policy.crypto_epoch,
            },
        )
        self.db.add(row)
        self.db.flush()
        self._audit("quorum_created", row, reason_code="created")
        self._metric("bastion_quorum_created_total", policy, "pending", "created")
        return quorum_hash, initial

    def submit_approval(
        self,
        *,
        quorum_hash: str,
        approval: VerifiedQuorumApproval,
    ) -> QuorumEvaluation:
        try:
            return self._submit_approval(quorum_hash=quorum_hash, approval=approval)
        except QuorumError as exc:
            row = self._locked_row(quorum_hash)
            policy = _policy_from_payload((row.metadata_json or {}).get("policy"))
            reason = str(exc)
            event = (
                "quorum_duplicate_participant_rejected"
                if reason
                in {
                    QuorumFailureReason.DUPLICATE_PRINCIPAL.value,
                    QuorumFailureReason.DUPLICATE_UNDERLYING_KEY.value,
                    QuorumFailureReason.DUPLICATE_DEVICE.value,
                }
                else "quorum_approval_rejected"
            )
            self._audit(event, row, reason_code=reason, approval=approval)
            self._metric("bastion_quorum_approvals_total", policy, "deny", reason)
            raise

    def _submit_approval(
        self,
        *,
        quorum_hash: str,
        approval: VerifiedQuorumApproval,
    ) -> QuorumEvaluation:
        with self.db.begin_nested():
            row = self._locked_row(quorum_hash)
            policy = _policy_from_payload((row.metadata_json or {}).get("policy"))
            self._ensure_open(row)
            self._validate_approval(row, policy, approval)
            approvals = self._approvals(row)
            self._reject_duplicates(approvals, approval)
            compatibility_count = sum(
                item.get("verification_strength") == "compatibility" for item in approvals
            ) + (approval.verification_strength == "compatibility")
            if compatibility_count > policy.maximum_compatibility_proofs:
                raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)
            slot = self._select_slot(policy, approvals, approval)
            if slot is None:
                raise QuorumError(QuorumFailureReason.PARTICIPANT_NOT_ALLOWED.value)
            revoked = self.revocations.check_quorum_targets(
                quorum_policy=policy.policy_hash,
                quorum_attempt=row.quorum_hash,
                quorum_approval=approval.approval_hash,
                principal=approval.principal_hash,
                underlying_key=approval.underlying_key_hash,
                device=approval.device_fingerprint,
                proof=approval.proof_hash,
            )
            if any(bool(value) for value in revoked.values()):
                raise QuorumError(QuorumFailureReason.PROOF_REVOKED.value)
            stored = _approval_payload(approval, slot.slot_id)
            approvals.append(stored)
            metadata = dict(row.metadata_json or {})
            metadata["approvals"] = approvals
            row.metadata_json = metadata
            row.participant_hashes_json = [str(item["principal_hash"]) for item in approvals]
            evaluation = self._evaluate(row, policy, approvals)
            if evaluation.status is QuorumStatus.SATISFIED:
                allowed, reason = self.policy_authorizer.authorize_quorum(
                    action="quorum_satisfy", policy=policy, evaluation=evaluation
                )
                if not allowed:
                    row.status = QuorumStatus.DENIED.value
                    self._audit("quorum_policy_denied", row, reason_code=reason)
                    raise QuorumError(QuorumDecision.POLICY_DENIED.value)
                metadata["satisfied_at"] = self.clock().isoformat()
                metadata["cooldown_until"] = (
                    self.clock() + timedelta(seconds=policy.cooldown_seconds)
                ).isoformat()
                row.metadata_json = metadata
            row.status = evaluation.status.value
            row.updated_at = self.clock()
            self.db.flush()
            self._audit(
                "quorum_satisfied"
                if evaluation.status is QuorumStatus.SATISFIED
                else "quorum_approval_recorded",
                row,
                reason_code=evaluation.reason_code,
                approval=approval,
                slot_id=slot.slot_id,
            )
            self._metric(
                "bastion_quorum_approvals_total",
                policy,
                evaluation.status.value,
                evaluation.reason_code,
            )
            return replace(
                evaluation,
                cooldown_until=(row.metadata_json or {}).get("cooldown_until"),
            )

    def evaluate(self, quorum_hash: str) -> QuorumEvaluation:
        row = self._locked_row(quorum_hash)
        self._ensure_not_terminal_or_expire(row, allow_satisfied=True)
        return self._evaluate_row(row)

    def to_step_up_state(self, quorum_hash: str) -> QuorumState:
        """Project safe quorum evidence into the existing step-up policy input."""
        row = self._locked_row(quorum_hash)
        evaluation = self.evaluate(quorum_hash)
        approvals = self._approvals(row)
        satisfied_at = _parse_datetime(
            (row.metadata_json or {}).get("satisfied_at") or self.clock().isoformat()
        )
        return QuorumState(
            threshold=evaluation.threshold,
            participants=evaluation.approval_count,
            signer_principal_hashes=tuple(str(item["principal_hash"]) for item in approvals),
            intent_hash=str((row.metadata_json or {}).get("intent_hash")),
            freshness_seconds=max(0, int((self.clock() - satisfied_at).total_seconds())),
            distinct_roles=tuple(
                sorted({str(item["role"]) for item in approvals if item.get("role")})
            ),
        )

    def authorize_and_consume(self, *, quorum_hash: str, action: str) -> QuorumEvaluation:
        with self.db.begin_nested():
            row = self._locked_row(quorum_hash)
            self._ensure_not_terminal_or_expire(row, allow_satisfied=True)
            policy = _policy_from_payload((row.metadata_json or {}).get("policy"))
            if action != policy.action:
                raise QuorumError(QuorumFailureReason.ACTION_MISMATCH.value)
            evaluation = self._evaluate(row, policy, self._approvals(row))
            if evaluation.status is not QuorumStatus.SATISFIED:
                raise QuorumError("quorum_not_satisfied")
            cooldown_until = _parse_datetime((row.metadata_json or {}).get("cooldown_until"))
            if cooldown_until and cooldown_until > self.clock():
                raise QuorumError("quorum_cooldown_active")
            revoked = self.revocations.check_quorum_targets(
                quorum_policy=policy.policy_hash,
                quorum_attempt=row.quorum_hash,
            )
            if any(bool(value) for value in revoked.values()):
                row.status = QuorumStatus.REVOKED.value
                raise QuorumError(QuorumDecision.QUORUM_REVOKED.value)
            allowed, reason = self.policy_authorizer.authorize_quorum(
                action=policy.action, policy=policy, evaluation=evaluation
            )
            if not allowed:
                raise QuorumError(reason or QuorumDecision.POLICY_DENIED.value)
            if policy.one_time:
                row.status = QuorumStatus.CONSUMED.value
                metadata = dict(row.metadata_json or {})
                metadata["consumed_at"] = self.clock().isoformat()
                row.metadata_json = metadata
                row.updated_at = self.clock()
                self.db.flush()
            self._audit("quorum_consumed", row, reason_code="quorum_authorized")
            self._metric("bastion_quorum_decisions_total", policy, "allow", "satisfied")
            return replace(
                evaluation, decision=QuorumDecision.ALLOW, reason_code="quorum_authorized"
            )

    def revoke(self, quorum_hash: str, *, reason_code: str) -> None:
        row = self._locked_row(quorum_hash)
        if row.status in {QuorumStatus.CONSUMED.value, QuorumStatus.REVOKED.value}:
            return
        row.status = QuorumStatus.REVOKED.value
        row.revoked_at = self.clock()
        row.updated_at = self.clock()
        self.db.flush()
        self._audit("quorum_revoked", row, reason_code=reason_code)

    def _validate_approval(
        self, row: MultiWalletQuorum, policy: QuorumPolicy, approval: VerifiedQuorumApproval
    ) -> None:
        now = self.clock()
        if not approval.cryptographically_verified:
            raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)
        if approval.action != policy.action:
            raise QuorumError(QuorumFailureReason.ACTION_MISMATCH.value)
        if not hmac.compare_digest(approval.policy_hash, policy.policy_hash):
            raise QuorumError(QuorumFailureReason.POLICY_MISMATCH.value)
        if not hmac.compare_digest(
            approval.intent_hash, str((row.metadata_json or {}).get("intent_hash", ""))
        ):
            raise QuorumError("intent_mismatch")
        if approval.principal_type not in policy.allowed_principal_types:
            raise QuorumError(QuorumFailureReason.PARTICIPANT_NOT_ALLOWED.value)
        if (
            approval.proof_method not in policy.allowed_proof_methods
            or approval.proof_method in policy.forbidden_proof_methods
        ):
            raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)
        if _parse_datetime(approval.expires_at) <= now:
            raise QuorumError(QuorumFailureReason.PROOF_EXPIRED.value)
        compatibility = approval.verification_strength == "compatibility"
        if compatibility and policy.maximum_compatibility_proofs == 0:
            raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)
        if (
            approval.proof_method is QuorumProofMethod.LEGACY_MESSAGE_SIGNATURE
            and policy.risk_level
            in {
                "critical",
                "sovereign",
            }
        ):
            raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)
        if approval.proof_method is QuorumProofMethod.LNURL_AUTH and policy.action in {
            "treasury_policy_change",
            "issuer_key_rotation",
        }:
            raise QuorumError(QuorumFailureReason.PROOF_TOO_WEAK.value)

    def _reject_duplicates(
        self, approvals: list[dict[str, object]], candidate: VerifiedQuorumApproval
    ) -> None:
        for approval in approvals:
            if hmac.compare_digest(str(approval["principal_hash"]), candidate.principal_hash):
                raise QuorumError(QuorumFailureReason.DUPLICATE_PRINCIPAL.value)
            if hmac.compare_digest(
                str(approval["underlying_key_hash"]), candidate.underlying_key_hash
            ):
                raise QuorumError(QuorumFailureReason.DUPLICATE_UNDERLYING_KEY.value)
            existing_device = approval.get("device_fingerprint")
            if (
                existing_device
                and candidate.device_fingerprint
                and hmac.compare_digest(str(existing_device), candidate.device_fingerprint)
            ):
                raise QuorumError(QuorumFailureReason.DUPLICATE_DEVICE.value)

    def _select_slot(
        self,
        policy: QuorumPolicy,
        approvals: list[dict[str, object]],
        approval: VerifiedQuorumApproval,
    ) -> QuorumParticipantSlot | None:
        filled = {str(item["slot_id"]) for item in approvals}
        for slot in policy.participant_slots:
            if slot.slot_id in filled:
                continue
            if slot.required_role and slot.required_role != approval.role:
                continue
            if (
                slot.allowed_principal_types
                and approval.principal_type not in slot.allowed_principal_types
            ):
                continue
            if (
                slot.allowed_proof_methods
                and approval.proof_method not in slot.allowed_proof_methods
            ):
                continue
            if (
                slot.required_participant_type
                and approval.participant_type is not slot.required_participant_type
            ):
                continue
            if slot.require_hardware_evidence and not approval.hardware_evidence_verified:
                continue
            return slot
        return None

    def _evaluate_row(self, row: MultiWalletQuorum) -> QuorumEvaluation:
        return self._evaluate(
            row,
            _policy_from_payload((row.metadata_json or {}).get("policy")),
            self._approvals(row),
        )

    def _evaluate(
        self,
        row: MultiWalletQuorum,
        policy: QuorumPolicy,
        approvals: list[dict[str, object]],
    ) -> QuorumEvaluation:
        if row.status == QuorumStatus.REVOKED.value:
            return _terminal_evaluation(policy, QuorumStatus.REVOKED, QuorumDecision.QUORUM_REVOKED)
        if _parse_datetime((row.metadata_json or {}).get("expires_at")) <= self.clock():
            row.status = QuorumStatus.EXPIRED.value
            return _terminal_evaluation(policy, QuorumStatus.EXPIRED, QuorumDecision.QUORUM_EXPIRED)
        principals = {str(item["principal_hash"]) for item in approvals}
        methods = {str(item["proof_method"]) for item in approvals}
        roles = {str(item["role"]) for item in approvals if item.get("role")}
        participant_types = {str(item["participant_type"]) for item in approvals}
        hardware = any(
            bool(item.get("hardware_evidence_verified"))
            and item.get("proof_method")
            in {QuorumProofMethod.HARDWARE_WALLET.value, QuorumProofMethod.AIR_GAPPED.value}
            for item in approvals
        )
        missing_roles = sorted(policy.required_roles - roles)
        missing_methods = sorted(
            item.value for item in policy.required_methods if item.value not in methods
        )
        missing_types = sorted(
            item.value
            for item in policy.required_participant_types
            if item.value not in participant_types
        )
        reason = "quorum_satisfied"
        satisfied = len(approvals) >= policy.threshold
        if len(principals) < policy.minimum_distinct_principals:
            satisfied, reason = False, QuorumFailureReason.INSUFFICIENT_DISTINCT_PRINCIPALS.value
        elif len(methods) < policy.minimum_distinct_methods:
            satisfied, reason = False, QuorumFailureReason.INSUFFICIENT_DISTINCT_METHODS.value
        elif missing_roles:
            satisfied, reason = False, QuorumFailureReason.REQUIRED_ROLE_MISSING.value
        elif missing_methods or missing_types:
            satisfied, reason = False, "required_quorum_evidence_missing"
        elif policy.require_hardware_wallet and not hardware:
            satisfied, reason = False, QuorumFailureReason.REQUIRED_HARDWARE_PROOF_MISSING.value
        elif policy.require_air_gapped_proof and QuorumProofMethod.AIR_GAPPED.value not in methods:
            satisfied, reason = False, "required_air_gapped_proof_missing"
        elif (
            policy.require_transparency_checkpoint
            and QuorumProofMethod.TRANSPARENCY_CHECKPOINT.value not in methods
        ):
            satisfied = False
            reason = QuorumFailureReason.REQUIRED_TRANSPARENCY_CHECKPOINT_MISSING.value
        status = (
            QuorumStatus.SATISFIED
            if satisfied
            else QuorumStatus.PARTIALLY_SATISFIED
            if approvals
            else QuorumStatus.PENDING
        )
        decision = (
            QuorumDecision.ALLOW
            if satisfied
            else QuorumDecision.ADDITIONAL_PARTICIPANT_REQUIRED
            if approvals
            else QuorumDecision.PENDING
        )
        return QuorumEvaluation(
            status,
            decision,
            reason if approvals or satisfied else "quorum_pending",
            policy.threshold,
            len(approvals),
            len(principals),
            len(methods),
            tuple(str(item["slot_id"]) for item in approvals),
            tuple(missing_roles),
            tuple(missing_methods),
            tuple(missing_types),
            (row.metadata_json or {}).get("cooldown_until"),
            policy.policy_hash,
        )

    def _ensure_open(self, row: MultiWalletQuorum) -> None:
        self._ensure_not_terminal_or_expire(row, allow_satisfied=False)

    def _ensure_not_terminal_or_expire(
        self, row: MultiWalletQuorum, *, allow_satisfied: bool
    ) -> None:
        expires = _parse_datetime((row.metadata_json or {}).get("expires_at"))
        if expires <= self.clock():
            row.status = QuorumStatus.EXPIRED.value
            self.db.flush()
            raise QuorumError(QuorumFailureReason.QUORUM_EXPIRED.value)
        blocked = {
            QuorumStatus.EXPIRED.value,
            QuorumStatus.DENIED.value,
            QuorumStatus.REVOKED.value,
            QuorumStatus.CANCELLED.value,
            QuorumStatus.CONSUMED.value,
            QuorumStatus.LOCKED.value,
        }
        if not allow_satisfied:
            blocked.add(QuorumStatus.SATISFIED.value)
        if row.status in blocked:
            reason = (
                QuorumFailureReason.QUORUM_CONSUMED.value
                if row.status == QuorumStatus.CONSUMED.value
                else f"quorum_{row.status}"
            )
            raise QuorumError(reason)

    def _locked_row(self, quorum_hash: str) -> MultiWalletQuorum:
        row = self.db.execute(
            select(MultiWalletQuorum)
            .where(MultiWalletQuorum.quorum_hash == quorum_hash)
            .with_for_update()
        ).scalar_one_or_none()
        if row is None:
            raise QuorumError("quorum_not_found")
        return row

    def _find_idempotent(self, idempotency_key_hash: str) -> MultiWalletQuorum | None:
        rows = self.db.execute(select(MultiWalletQuorum)).scalars()
        return next(
            (
                row
                for row in rows
                if (row.metadata_json or {}).get("idempotency_key_hash") == idempotency_key_hash
            ),
            None,
        )

    @staticmethod
    def _approvals(row: MultiWalletQuorum) -> list[dict[str, object]]:
        values = (row.metadata_json or {}).get("approvals", [])
        if not isinstance(values, list) or not all(isinstance(item, dict) for item in values):
            raise QuorumError("quorum_approvals_invalid")
        return [dict(item) for item in values]

    def _audit(
        self,
        event_type: str,
        row: MultiWalletQuorum,
        *,
        reason_code: str,
        approval: VerifiedQuorumApproval | None = None,
        slot_id: str | None = None,
    ) -> None:
        self.audit.record_event(
            event_type=event_type,
            actor_hash=row.principal_hash,
            object_hash=row.quorum_hash,
            metadata={
                "quorum_type": row.quorum_type,
                "policy_hash": row.policy_hash,
                "reason_code": reason_code,
                "approval_hash": approval.approval_hash if approval else None,
                "proof_method": approval.proof_method.value if approval else None,
                "participant_type": approval.participant_type.value if approval else None,
                "slot_id": slot_id,
            },
        )

    def _metric(self, name: str, policy: QuorumPolicy, result: str, reason: str) -> None:
        if self.metric_emitter:
            try:
                self.metric_emitter(
                    name,
                    {
                        "quorum_type": policy.quorum_type.value,
                        "action_group": str(policy.metadata.get("action_group", "unknown")),
                        "result": result,
                        "reason_code": reason,
                    },
                )
            except Exception:
                pass


class RecoveryCapsuleQuorumAdapter:
    """Connects Recovery Capsule's existing quorum boundary to this engine."""

    def __init__(
        self,
        service: WalletQuorumService,
        quorum_hash_for_capsule: Callable[[RecoveryCapsule], str | None] | None = None,
    ) -> None:
        self.service = service
        self.quorum_hash_for_capsule = quorum_hash_for_capsule or (
            lambda capsule: capsule.quorum_policy_id
        )

    def satisfied(self, *, capsule: RecoveryCapsule) -> bool:
        quorum_hash = self.quorum_hash_for_capsule(capsule)
        if not quorum_hash:
            return False
        try:
            evaluation = self.service.evaluate(quorum_hash)
        except QuorumError:
            return False
        return evaluation.status is QuorumStatus.SATISFIED


def _approval_payload(approval: VerifiedQuorumApproval, slot_id: str) -> dict[str, object]:
    return {
        "approval_hash": approval.approval_hash,
        "slot_id": slot_id,
        "participant_type": approval.participant_type.value,
        "principal_type": approval.principal_type.value,
        "principal_hash": approval.principal_hash,
        "underlying_key_hash": approval.underlying_key_hash,
        "proof_method": approval.proof_method.value,
        "proof_hash": approval.proof_hash,
        "verification_strength": approval.verification_strength,
        "verified_at": approval.verified_at,
        "expires_at": approval.expires_at,
        "intent_hash": approval.intent_hash,
        "action": approval.action,
        "policy_hash": approval.policy_hash,
        "role": approval.role,
        "device_fingerprint": approval.device_fingerprint,
        "hardware_evidence_verified": approval.hardware_evidence_verified,
        "limitations": list(approval.limitations),
    }


def _policy_from_payload(value: object) -> QuorumPolicy:
    if not isinstance(value, dict):
        raise QuorumError("quorum_policy_invalid")
    try:
        slots = tuple(
            QuorumParticipantSlot(
                slot_id=str(item["slot_id"]),
                required_role=item.get("required_role"),
                allowed_principal_types=frozenset(
                    QuorumParticipantType(candidate)
                    for candidate in item.get("allowed_principal_types", [])
                ),
                allowed_proof_methods=frozenset(
                    QuorumProofMethod(candidate)
                    for candidate in item.get("allowed_proof_methods", [])
                ),
                required_participant_type=(
                    QuorumParticipantType(item["required_participant_type"])
                    if item.get("required_participant_type")
                    else None
                ),
                require_hardware_evidence=bool(item.get("require_hardware_evidence")),
            )
            for item in value["participant_slots"]
        )
        return QuorumPolicy(
            policy_id=str(value["policy_id"]),
            version=int(value["version"]),
            quorum_type=QuorumType(value["quorum_type"]),
            action=str(value["action"]),
            threshold=int(value["threshold"]),
            participant_slots=slots,
            minimum_distinct_principals=int(value["minimum_distinct_principals"]),
            minimum_distinct_methods=int(value["minimum_distinct_methods"]),
            allowed_principal_types=frozenset(
                QuorumParticipantType(item) for item in value["allowed_principal_types"]
            ),
            allowed_proof_methods=frozenset(
                QuorumProofMethod(item) for item in value["allowed_proof_methods"]
            ),
            forbidden_proof_methods=frozenset(
                QuorumProofMethod(item) for item in value.get("forbidden_proof_methods", [])
            ),
            required_roles=frozenset(str(item) for item in value.get("required_roles", [])),
            required_methods=frozenset(
                QuorumProofMethod(item) for item in value.get("required_methods", [])
            ),
            required_participant_types=frozenset(
                QuorumParticipantType(item) for item in value.get("required_participant_types", [])
            ),
            maximum_compatibility_proofs=int(value.get("maximum_compatibility_proofs", 0)),
            require_hardware_wallet=bool(value.get("require_hardware_wallet")),
            require_air_gapped_proof=bool(value.get("require_air_gapped_proof")),
            require_active_pop_session=bool(value.get("require_active_pop_session", True)),
            require_human_intent=bool(value.get("require_human_intent", True)),
            require_recovery_capsule=bool(value.get("require_recovery_capsule")),
            require_transparency_checkpoint=bool(value.get("require_transparency_checkpoint")),
            expires_in_seconds=int(value.get("expires_in_seconds", 300)),
            cooldown_seconds=int(value.get("cooldown_seconds", 0)),
            policy_epoch=int(value.get("policy_epoch", 1)),
            crypto_epoch=int(value.get("crypto_epoch", 1)),
            risk_level=str(value.get("risk_level", "critical")),
            one_time=bool(value.get("one_time", True)),
            metadata=dict(value.get("metadata", {})),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise QuorumError("quorum_policy_invalid") from exc


def _parse_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise QuorumError("quorum_timestamp_invalid")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _terminal_evaluation(
    policy: QuorumPolicy, status: QuorumStatus, decision: QuorumDecision
) -> QuorumEvaluation:
    return QuorumEvaluation(
        status,
        decision,
        decision.value,
        policy.threshold,
        0,
        0,
        0,
        (),
        policy_hash=policy.policy_hash,
    )


__all__ = [
    "AccessPolicyEngineQuorumAuthorizer",
    "QuorumError",
    "RecoveryCapsuleQuorumAdapter",
    "WalletQuorumService",
]
