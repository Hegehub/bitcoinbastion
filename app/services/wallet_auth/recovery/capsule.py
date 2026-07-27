"""Transactional Recovery Capsule orchestration over the existing wallet-auth model."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.wallet_auth import RecoveryCapsule as RecoveryCapsuleRow
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import (
    hmac_sha256_prefixed,
    secure_nonce_hex,
    sha256_prefixed,
)
from app.services.wallet_auth.recovery.cooldown import RecoveryCooldownService
from app.services.wallet_auth.recovery.errors import (
    RecoveryCapsuleError,
    RecoveryCooldownError,
    RecoveryPolicyError,
)
from app.services.wallet_auth.recovery.factor_registry import RecoveryFactorRegistry
from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryCapsuleStatus as S,
    RecoveryCompletionResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryProfile,
    RecoveryVerificationContext,
)
from app.services.wallet_auth.recovery.policy import (
    PROFILE_REQUIREMENTS,
    QuorumVerifierBoundary,
    RecoveryPolicyAuthorizer,
    factors_satisfy_profile,
)
from app.services.wallet_auth.recovery.redaction import safe_recovery_metadata
from app.services.wallet_auth.recovery.state_machine import transition

MetricEmitter = Callable[[str, dict[str, str]], None]


class RecoveryArtifactManager(Protocol):
    def secure_after_recovery(self, *, capsule: RecoveryCapsule) -> tuple[str, ...]: ...


class RecoveryRevocationResolver(Protocol):
    def check(
        self,
        *,
        capsule: RecoveryCapsule,
        factor_type: RecoveryFactorType | None = None,
        replay_reference_hash: str | None = None,
    ) -> dict[str, object]: ...


class RecoveryFactorReceiptValidator(Protocol):
    def validate_stored_receipt(self, receipt: dict[str, object]) -> bool: ...


class RecoveryCapsuleService:
    def __init__(
        self,
        db: Session,
        *,
        server_pepper: str,
        factor_registry: RecoveryFactorRegistry,
        policy_authorizer: RecoveryPolicyAuthorizer,
        revocation_resolver: RecoveryRevocationResolver,
        artifact_manager: RecoveryArtifactManager,
        quorum_verifier: QuorumVerifierBoundary | None = None,
        cooldown_service: RecoveryCooldownService | None = None,
        audit_chain: AccessAuditChain | None = None,
        metric_emitter: MetricEmitter | None = None,
        maximum_attempts: int = 5,
        max_capsules_per_day: int = 3,
        capsule_ttl_seconds: int = 604800,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not server_pepper:
            raise RecoveryCapsuleError("recovery_capsule_pepper_required")
        self.db, self.server_pepper, self.factor_registry = db, server_pepper, factor_registry
        self.policy_authorizer, self.revocation_resolver, self.artifact_manager = (
            policy_authorizer,
            revocation_resolver,
            artifact_manager,
        )
        self.quorum_verifier, self.cooldown = (
            quorum_verifier,
            cooldown_service or RecoveryCooldownService(),
        )
        self.audit, self.metric_emitter = audit_chain or AccessAuditChain(db), metric_emitter
        self.maximum_attempts, self.max_capsules_per_day, self.capsule_ttl_seconds = (
            maximum_attempts,
            max_capsules_per_day,
            capsule_ttl_seconds,
        )
        self.clock = clock or (lambda: datetime.now(UTC))
        self.factor_receipt_validator: RecoveryFactorReceiptValidator | None = None

    def set_factor_receipt_validator(self, validator: RecoveryFactorReceiptValidator) -> None:
        if self.factor_receipt_validator is not None:
            raise RecoveryCapsuleError("recovery_factor_receipt_validator_already_configured")
        self.factor_receipt_validator = validator

    def create(
        self,
        *,
        principal_id: int,
        principal_hash: str,
        principal_type: str,
        recovery_profile: RecoveryProfile,
        recovery_reason: str,
        requested_operations: tuple[str, ...],
        policy_epoch: int = 1,
        crypto_epoch: int = 1,
    ) -> RecoveryCapsule:
        now = self.clock()
        recent = self.db.execute(
            select(func.count(RecoveryCapsuleRow.id)).where(
                RecoveryCapsuleRow.principal_hash == principal_hash,
                RecoveryCapsuleRow.created_at >= now - timedelta(days=1),
            )
        ).scalar_one()
        if recent >= self.max_capsules_per_day:
            raise RecoveryCapsuleError("recovery_capsule_rate_limited")
        requirements = PROFILE_REQUIREMENTS[recovery_profile]
        capsule_id = f"rc_{secure_nonce_hex(16)}"
        capsule_hash = hmac_sha256_prefixed(self.server_pepper, capsule_id)
        metadata = {
            "capsule_id_hash": sha256_prefixed(capsule_id),
            "schema_version": 1,
            "crypto_epoch": crypto_epoch,
            "policy_epoch": policy_epoch,
            "principal_type": principal_type,
            "required_factor_count": requirements.required_factor_count,
            "quorum_policy_id": None,
            "trusted_device_requirement": requirements.trusted_device_requirement,
            "expires_at": (now + timedelta(seconds=self.capsule_ttl_seconds)).isoformat(),
            "attempt_count": 0,
            "maximum_attempts": self.maximum_attempts,
            "risk_level": "medium",
            "recovery_reason": recovery_reason,
            "requested_operations": list(requested_operations),
            "revoked_targets": [],
            "replay_references": [],
            "issuer_key_id": "recovery-capsule-issuer",
            "issuer_signature_metadata": {"status": "not_issued"},
        }
        row = RecoveryCapsuleRow(
            principal_id=principal_id,
            principal_hash=principal_hash,
            capsule_hash=capsule_hash,
            recovery_profile=recovery_profile.value,
            status=S.CREATED.value,
            required_factors_json=[
                factor.value for factor in sorted(requirements.required_factors, key=str)
            ],
            completed_factors_json=[],
            policy_hash=f"sha256:recovery-policy-{policy_epoch}",
            created_at=now,
            updated_at=now,
            metadata_json=safe_recovery_metadata(metadata),
        )
        self.db.add(row)
        self.db.flush()
        row.status = transition(S.CREATED, S.AWAITING_FACTORS).value
        allowed, _ = self.policy_authorizer.authorize(
            action="recovery_capsule_create", capsule=self._view(row)
        )
        if not allowed:
            self._set_status(row, S.FAILED)
            self._audit("recovery_capsule_creation_denied", row, {"reason_code": "policy_denied"})
            raise RecoveryPolicyError("recovery_policy_denied")
        self._audit(
            "recovery_capsule_created",
            row,
            {"recovery_profile": recovery_profile.value, "reason_code": "created"},
        )
        self._metric(
            "bastion_recovery_capsules_created_total",
            recovery_profile,
            principal_type,
            "success",
            "created",
        )
        return self._view(row)

    def get(self, capsule_hash: str) -> RecoveryCapsule:
        """Return the internal commitment-only view used by factor adapters."""
        return self._view(self._locked_row(capsule_hash))

    def bind_quorum(self, capsule_hash: str, quorum_hash: str) -> RecoveryCapsule:
        """Bind one commitment-only quorum attempt after central policy approval."""
        row = self._locked_row(capsule_hash)
        capsule = self._view(row)
        self._ensure_active(row, capsule)
        if not PROFILE_REQUIREMENTS[capsule.recovery_profile].requires_quorum:
            raise RecoveryCapsuleError("recovery_quorum_not_required")
        if capsule.quorum_policy_id and capsule.quorum_policy_id != quorum_hash:
            raise RecoveryCapsuleError("recovery_quorum_already_bound")
        allowed, _ = self.policy_authorizer.authorize(
            action="recovery_factor_accept", capsule=capsule
        )
        if not allowed:
            raise RecoveryPolicyError("recovery_policy_denied")
        metadata = dict(row.metadata_json or {})
        metadata["quorum_policy_id"] = quorum_hash
        row.metadata_json = safe_recovery_metadata(metadata)
        row.updated_at = self.clock()
        self.db.flush()
        self._audit("recovery_quorum_bound", row, {"reason_code": "quorum_bound"})
        return self._view(row)

    async def submit_factor(
        self, *, capsule_hash: str, submission: RecoveryFactorSubmission
    ) -> RecoveryCapsule:
        row = self._locked_row(capsule_hash)
        capsule = self._view(row)
        self._ensure_active(row, capsule)
        metadata = dict(row.metadata_json or {})
        attempts = int(metadata.get("attempt_count", 0))
        if attempts >= self.maximum_attempts:
            self._set_status(row, S.LOCKED)
            raise RecoveryCapsuleError("recovery_capsule_locked")
        replay = set(metadata.get("replay_references", []))
        revocation = self.revocation_resolver.check(
            capsule=capsule,
            factor_type=submission.factor_type,
            replay_reference_hash=submission.proof_reference_hash,
        )
        if revocation.get("capsule_revoked") or revocation.get("principal_recovery_forbidden"):
            raise RecoveryCapsuleError("recovery_revoked")
        revocation["replay_used"] = submission.proof_reference_hash in replay
        allowed, _ = self.policy_authorizer.authorize(
            action="recovery_factor_submit", capsule=capsule
        )
        if not allowed:
            self._audit(
                "recovery_factor_rejected",
                row,
                {
                    "factor_type": submission.factor_type.value,
                    "reason_code": "policy_denied",
                },
            )
            raise RecoveryPolicyError("recovery_policy_denied")
        self._set_status(row, S.FACTOR_VERIFICATION_IN_PROGRESS)
        self._audit("recovery_factor_submitted", row, {"factor_type": submission.factor_type.value})
        try:
            result = await self.factor_registry.verify(
                self._view(row),
                submission,
                RecoveryVerificationContext(
                    capsule.principal_hash, capsule.policy_epoch, revocation
                ),
            )
        except Exception as exc:
            metadata["attempt_count"] = attempts + 1
            row.metadata_json = metadata
            self._set_status(
                row, S.LOCKED if attempts + 1 >= self.maximum_attempts else S.AWAITING_FACTORS
            )
            reason = str(exc)
            event_type = (
                "recovery_factor_replay_rejected"
                if "replay" in reason
                else "recovery_duplicate_factor_rejected"
                if "duplicate" in reason
                else "recovery_factor_rejected"
            )
            self._audit(
                event_type,
                row,
                {"factor_type": submission.factor_type.value, "reason_code": "factor_rejected"},
            )
            raise
        completed = list(
            dict.fromkeys([*(row.completed_factors_json or []), result.factor_type.value])
        )
        tentative = replace(
            self._view(row),
            verified_factors=tuple(RecoveryFactorType(item) for item in completed),
        )
        allowed, _ = self.policy_authorizer.authorize(
            action="recovery_factor_accept", capsule=tentative
        )
        if not allowed:
            self._set_status(row, S.AWAITING_FACTORS)
            self._audit(
                "recovery_factor_rejected",
                row,
                {
                    "factor_type": result.factor_type.value,
                    "reason_code": "policy_denied",
                },
            )
            raise RecoveryPolicyError("recovery_policy_denied")
        replay.add(submission.proof_reference_hash)
        metadata["replay_references"] = sorted(replay)
        row.metadata_json = metadata
        row.completed_factors_json = completed
        receipts = list(metadata.get("factor_receipts", []))
        receipt = result.audit_metadata.get("factor_receipt")
        if isinstance(receipt, dict):
            receipts.append(receipt)
            metadata["factor_receipts"] = receipts
            row.metadata_json = safe_recovery_metadata(metadata)
        self._set_status(row, S.AWAITING_FACTORS)
        self._audit(
            "recovery_factor_verified",
            row,
            {
                "factor_type": result.factor_type.value,
                "factor_fingerprint": result.factor_fingerprint,
            },
        )
        current = self._view(row)
        requirements = PROFILE_REQUIREMENTS[current.recovery_profile]
        if factors_satisfy_profile(current, requirements):
            now = self.clock()
            expiry = self.cooldown.calculate_expiry(
                profile=current.recovery_profile,
                risk_level=current.risk_level,
                now=now,
                failed_attempts=int(metadata.get("attempt_count", 0)),
            )
            row.cooldown_until = expiry
            metadata["cooldown_started_at"] = now.isoformat()
            row.metadata_json = metadata
            self._set_status(row, S.COOLDOWN)
            self._audit("recovery_cooldown_started", row, {"cooldown_expires_at": expiry})
        return self._view(row)

    def complete(self, *, capsule_hash: str) -> RecoveryCompletionResult:
        with self.db.begin_nested():
            row = self._locked_row(capsule_hash)
            capsule = self._view(row)
            self._ensure_active(row, capsule)
            if capsule.status is S.COOLDOWN:
                if capsule.cooldown_expires_at and capsule.cooldown_expires_at > self.clock():
                    raise RecoveryCooldownError("recovery_cooldown_active")
                self._set_status(row, S.READY_FOR_COMPLETION)
                capsule = self._view(row)
                self._audit(
                    "recovery_ready_for_completion", row, {"reason_code": "cooldown_complete"}
                )
            if capsule.status is not S.READY_FOR_COMPLETION:
                raise RecoveryCapsuleError("recovery_not_ready")
            requirements = PROFILE_REQUIREMENTS[capsule.recovery_profile]
            if not factors_satisfy_profile(capsule, requirements):
                raise RecoveryCapsuleError("recovery_factors_incomplete")
            self._validate_factor_receipts(row)
            if requirements.requires_quorum and (
                self.quorum_verifier is None or not self.quorum_verifier.satisfied(capsule=capsule)
            ):
                raise RecoveryCapsuleError("recovery_quorum_incomplete")
            revocation = self.revocation_resolver.check(capsule=capsule)
            if revocation.get("capsule_revoked") or revocation.get("principal_recovery_forbidden"):
                raise RecoveryCapsuleError("recovery_revoked")
            allowed, reason = self.policy_authorizer.authorize(
                action="recovery_complete", capsule=capsule
            )
            self._audit("recovery_completion_requested", row, {"reason_code": reason})
            if not allowed:
                self._audit("recovery_completion_denied", row, {"reason_code": "policy_denied"})
                raise RecoveryPolicyError("recovery_policy_denied")
            revoked = self.artifact_manager.secure_after_recovery(capsule=capsule)
            metadata = dict(row.metadata_json or {})
            metadata["revoked_targets"] = list(revoked)
            row.metadata_json = metadata
            row.completed_at = self.clock()
            self._set_status(row, S.COMPLETED)
            self._audit(
                "recovery_completed",
                row,
                {"reason_code": "completed", "revoked_target_types": list(revoked)},
            )
            self._metric(
                "bastion_recovery_capsules_completed_total",
                capsule.recovery_profile,
                capsule.principal_type,
                "success",
                "completed",
            )
            return RecoveryCompletionResult(
                capsule.capsule_hash, S.COMPLETED, "recovery_only", tuple(revoked), True
            )

    def cancel(self, capsule_hash: str) -> RecoveryCapsule:
        row = self._locked_row(capsule_hash)
        self._set_status(row, S.CANCELLED)
        metadata = dict(row.metadata_json or {})
        metadata["cancelled_at"] = self.clock().isoformat()
        row.metadata_json = metadata
        self._audit("recovery_cancelled", row, {"reason_code": "user_cancelled"})
        return self._view(row)

    def _locked_row(self, capsule_hash: str) -> RecoveryCapsuleRow:
        row = self.db.execute(
            select(RecoveryCapsuleRow)
            .where(RecoveryCapsuleRow.capsule_hash == capsule_hash)
            .with_for_update()
        ).scalar_one_or_none()
        if row is None:
            raise RecoveryCapsuleError("recovery_capsule_not_found")
        return row

    def _ensure_active(self, row: RecoveryCapsuleRow, capsule: RecoveryCapsule) -> None:
        if capsule.expires_at <= self.clock():
            self._set_status(row, S.EXPIRED)
            self._audit("recovery_expired", row, {"reason_code": "expired"})
            raise RecoveryCapsuleError("recovery_capsule_expired")
        if capsule.status in {S.COMPLETED, S.FAILED, S.CANCELLED, S.EXPIRED, S.LOCKED, S.REVOKED}:
            raise RecoveryCapsuleError("recovery_capsule_not_active")

    def _set_status(self, row: RecoveryCapsuleRow, status: S) -> None:
        row.status = transition(S(row.status), status).value
        row.updated_at = self.clock()
        self.db.flush()

    def _validate_factor_receipts(self, row: RecoveryCapsuleRow) -> None:
        receipts = (row.metadata_json or {}).get("factor_receipts", [])
        if not isinstance(receipts, list):
            raise RecoveryCapsuleError("recovery_factor_receipt_invalid")
        now = self.clock()
        if receipts and self.factor_receipt_validator is None:
            raise RecoveryCapsuleError("recovery_factor_receipt_validator_unavailable")
        for receipt in receipts:
            if not isinstance(receipt, dict):
                raise RecoveryCapsuleError("recovery_factor_receipt_invalid")
            expires_at = _parse(receipt.get("expires_at"))
            if expires_at is None or expires_at <= now:
                raise RecoveryCapsuleError("recovery_factor_receipt_expired")
            if receipt.get("recovery_attempt_hash") != row.capsule_hash:
                raise RecoveryCapsuleError("recovery_factor_receipt_mismatch")
            if (
                self.factor_receipt_validator
                and not self.factor_receipt_validator.validate_stored_receipt(receipt)
            ):
                raise RecoveryCapsuleError("recovery_factor_receipt_signature_invalid")

    def _view(self, row: RecoveryCapsuleRow) -> RecoveryCapsule:
        data = row.metadata_json or {}
        created = _utc(row.created_at)
        updated = _utc(row.updated_at)
        return RecoveryCapsule(
            str(data.get("capsule_id_hash")),
            row.capsule_hash,
            int(data.get("schema_version", 1)),
            int(data.get("crypto_epoch", 1)),
            int(data.get("policy_epoch", 1)),
            row.principal_hash,
            str(data.get("principal_type", "unknown")),
            RecoveryProfile(row.recovery_profile),
            S(row.status),
            tuple(
                RecoveryFactorType(item)
                for item in row.required_factors_json or []
                if isinstance(item, str)
            ),
            tuple(
                RecoveryFactorType(item)
                for item in row.completed_factors_json or []
                if isinstance(item, str)
            ),
            int(data.get("required_factor_count", 1)),
            data.get("quorum_policy_id"),
            str(data.get("trusted_device_requirement", "optional")),
            _parse(data.get("cooldown_started_at")),
            _utc(row.cooldown_until) if row.cooldown_until else None,
            _parse(data.get("expires_at")) or created,
            int(data.get("attempt_count", 0)),
            int(data.get("maximum_attempts", 5)),
            str(data.get("risk_level", "medium")),
            str(data.get("recovery_reason", "unknown")),
            tuple(data.get("requested_operations", [])),
            tuple(data.get("revoked_targets", [])),
            created,
            updated,
            _utc(row.completed_at) if row.completed_at else None,
            _parse(data.get("cancelled_at")),
            str(data.get("issuer_key_id", "recovery-capsule-issuer")),
            dict(data.get("issuer_signature_metadata", {})),
            data.get("audit_chain_head"),
            row.transparency_checkpoint_hash,
            row.policy_hash or f"sha256:recovery-policy-{int(data.get('policy_epoch', 1))}",
        )

    def _audit(self, event_type: str, row: RecoveryCapsuleRow, metadata: dict[str, object]) -> None:
        event = self.audit.record_event(
            event_type=event_type,
            actor_hash=row.principal_hash,
            object_hash=row.capsule_hash,
            metadata={"recovery_profile": row.recovery_profile, **metadata},
        )
        data = dict(row.metadata_json or {})
        data["audit_chain_head"] = event.event_hash
        row.metadata_json = data

    def _metric(
        self, name: str, profile: RecoveryProfile, principal_type: str, result: str, reason: str
    ) -> None:
        if self.metric_emitter:
            try:
                self.metric_emitter(
                    name,
                    {
                        "recovery_profile": profile.value,
                        "principal_type": principal_type,
                        "result": result,
                        "reason_code": reason,
                    },
                )
            except Exception:
                return


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _parse(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _utc(parsed)
