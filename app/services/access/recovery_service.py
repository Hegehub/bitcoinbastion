"""Production foundation for Bastion Proof-of-Access recovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import (
    AccessDevice,
    AccessSession,
    RecoveryAttempt,
    RecoveryAttemptStatus,
    RecoveryQuorum,
)
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import hmac_sha256_prefixed, secure_nonce_hex, sha256_prefixed
from app.services.access.recovery_policy import RecoveryPolicy
from app.services.access.recovery_quorum import (
    RecoveryFactorType,
    evaluate_recovery_quorum,
    recovery_quorum_profile,
)
from app.services.access.recovery_seed import (
    RECOVERY_SAFETY_WARNING,
    RecoveryPhraseStrength,
    generate_recovery_phrase,
    recovery_phrase_commitment,
    reject_bitcoin_wallet_seed_warning,
)
from app.services.access.revocation_registry import RevocationRegistry


@dataclass(frozen=True)
class RecoveryStartResult:
    recovery_attempt_id: str
    required_factors: list[str]
    allowed_factors: list[str]
    threshold: int
    cooldown_until: datetime
    safety_warnings: list[str]
    status: str


@dataclass(frozen=True)
class RecoveryFactorResult:
    recovery_attempt_id: str
    status: str
    verified_factors: list[str]
    threshold: int
    decision: str
    reason: str


@dataclass(frozen=True)
class RecoveryStatusResult:
    recovery_attempt_id: str
    status: str
    threshold: int
    verified_factor_count: int
    missing_factor_count: int
    decision: str
    reason: str
    cooldown_until: datetime | None


@dataclass(frozen=True)
class RecoveryCompleteResult:
    recovery_attempt_id: str
    status: str
    certificate_fingerprint: str | None
    device_key_fingerprint: str | None
    old_sessions_revoked: int
    safety_warnings: list[str]


@dataclass(frozen=True)
class RecoveryRotateResult:
    recovery_factor_id: str
    phrase_words: list[str]
    word_count: int
    factor_commitment: str
    warning: str
    display_once: bool


class RecoveryError(ValueError):
    pass


class AccessRecoveryService:
    def __init__(
        self,
        db: Session,
        *,
        server_pepper: str,
        cooldown_seconds: int = 900,
        max_attempts_per_hour: int = 5,
        audit_chain: AccessAuditChain | None = None,
        revocation_registry: RevocationRegistry | None = None,
    ) -> None:
        if not server_pepper:
            raise RecoveryError("recovery_pepper_required")
        self.db = db
        self.server_pepper = server_pepper
        self.cooldown_seconds = cooldown_seconds
        self.policy = RecoveryPolicy(max_attempts_per_hour=max_attempts_per_hour)
        self.audit_chain = audit_chain or AccessAuditChain(db)
        self.revocations = revocation_registry or RevocationRegistry()

    def setup_recovery(
        self,
        *,
        pass_lookup_hash: str,
        certificate_fingerprint: str | None,
        plan_code: PlanCode | str,
    ) -> RecoveryRotateResult:
        plan = normalize_plan_code(plan_code)
        strength = _strength_for_plan(plan)
        phrase = generate_recovery_phrase(strength)
        commitment = recovery_phrase_commitment(phrase.phrase, self.server_pepper)
        profile = recovery_quorum_profile(plan, cooldown_seconds=self.cooldown_seconds)
        factor_type = _phrase_factor_for_plan(plan)
        factor_entries = [
            {
                "recovery_factor_id": sha256_prefixed(f"{pass_lookup_hash}:{factor_type.value}"),
                "factor_type": factor_type.value,
                "factor_commitment": commitment,
                "factor_hint": f"Bastion Recovery Seed ({phrase.word_count} words)",
                "strength": strength.value,
                "status": "active",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ]
        for allowed_factor in profile.allowed_factors:
            if allowed_factor == factor_type or "phrase" in allowed_factor.value or allowed_factor == RecoveryFactorType.BUSINESS_RECOVERY_SEED:
                continue
            factor_entries.append(
                {
                    "recovery_factor_id": sha256_prefixed(f"{pass_lookup_hash}:{allowed_factor.value}"),
                    "factor_type": allowed_factor.value,
                    "factor_commitment": hmac_sha256_prefixed(
                        self.server_pepper,
                        f"recovery_factor:{allowed_factor.value}:{allowed_factor.value}-proof",
                    ),
                    "factor_hint": f"{allowed_factor.value} proof",
                    "strength": "device_or_vault_proof",
                    "status": "active",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        quorum = RecoveryQuorum(
            pass_lookup_hash=pass_lookup_hash,
            certificate_fingerprint=certificate_fingerprint,
            quorum_type=f"{plan.value}_recovery",
            threshold_required=profile.threshold,
            total_factors=len(profile.allowed_factors),
            factors_json=factor_entries,
            status="active",
            policy_json={"allowed_factors": [factor.value for factor in profile.allowed_factors]},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(quorum)
        self.db.flush()
        self._audit("recovery_setup_created", pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, metadata={"plan_code": plan.value})
        return RecoveryRotateResult(
            recovery_factor_id=sha256_prefixed(f"{pass_lookup_hash}:{factor_type.value}"),
            phrase_words=phrase.words,
            word_count=phrase.word_count,
            factor_commitment=commitment,
            warning=phrase.warning,
            display_once=True,
        )

    def start_recovery(
        self,
        *,
        pass_lookup_hash: str,
        declared_plan_code: PlanCode | str,
        certificate_fingerprint: str | None = None,
        new_device_key_fingerprint: str | None = None,
        recovery_reason: str = "device_recovery",
    ) -> RecoveryStartResult:
        plan = normalize_plan_code(declared_plan_code)
        self._reject_revoked(pass_lookup_hash, certificate_fingerprint)
        quorum = self._get_or_create_quorum(pass_lookup_hash, certificate_fingerprint, plan)
        profile = recovery_quorum_profile(plan, cooldown_seconds=self.cooldown_seconds)
        now = datetime.now(UTC)
        attempt_hash = hmac_sha256_prefixed(self.server_pepper, f"recovery_attempt:{secure_nonce_hex()}:{pass_lookup_hash}")
        cooldown_until = now + timedelta(seconds=self.cooldown_seconds)
        attempt = RecoveryAttempt(
            pass_lookup_hash=pass_lookup_hash,
            recovery_quorum_id=quorum.id,
            attempt_hash=attempt_hash,
            status=RecoveryAttemptStatus.STARTED.value,
            verified_factors_json=[],
            failed_factor_count=0,
            cooldown_until=cooldown_until,
            created_at=now,
            updated_at=now,
            metadata_json={
                "declared_plan_code": plan.value,
                "certificate_fingerprint": certificate_fingerprint,
                "new_device_key_fingerprint": new_device_key_fingerprint,
                "recovery_reason": recovery_reason,
            },
        )
        self.db.add(attempt)
        self.db.flush()
        self._audit("recovery_started", pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, metadata={"attempt_hash": attempt_hash, "reason": recovery_reason})
        self._audit("recovery_cooldown_started", pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, metadata={"attempt_hash": attempt_hash})
        return RecoveryStartResult(
            recovery_attempt_id=attempt_hash,
            required_factors=[factor.value for factor in profile.required_factors],
            allowed_factors=[factor.value for factor in profile.allowed_factors],
            threshold=profile.threshold,
            cooldown_until=cooldown_until,
            safety_warnings=[RECOVERY_SAFETY_WARNING],
            status=attempt.status,
        )

    def verify_recovery_factor(
        self,
        *,
        recovery_attempt_id: str,
        factor_type: str,
        recovery_factor: str,
    ) -> RecoveryFactorResult:
        attempt = self._get_attempt(recovery_attempt_id)
        if attempt.status in {RecoveryAttemptStatus.COMPLETED.value, RecoveryAttemptStatus.CANCELLED.value, RecoveryAttemptStatus.LOCKED.value}:
            raise RecoveryError("recovery_attempt_not_active")
        try:
            factor = RecoveryFactorType(factor_type)
        except ValueError as exc:
            raise RecoveryError("recovery_factor_invalid") from exc
        quorum = self._get_quorum(attempt)
        profile = recovery_quorum_profile(
            (attempt.metadata_json or {}).get("declared_plan_code", PlanCode.LITE.value),
            cooldown_seconds=self.cooldown_seconds,
        )
        if factor not in profile.allowed_factors:
            self._factor_failed(attempt, "recovery_factor_not_allowed")
            raise RecoveryError("recovery_factor_invalid")
        factor_valid = self._verify_factor_value(quorum, factor, recovery_factor)
        decision = self.policy.evaluate_factor(
            factor_valid=factor_valid, failed_factor_count=attempt.failed_factor_count
        )
        if not decision.allowed:
            self._factor_failed(attempt, decision.reason)
            raise RecoveryError(decision.reason)
        verified = _verified_factor_values(attempt.verified_factors_json)
        if factor.value not in verified:
            verified.append(factor.value)
        attempt.verified_factors_json = verified
        attempt.status = RecoveryAttemptStatus.FACTOR_VERIFIED.value
        attempt.updated_at = datetime.now(UTC)
        evaluation = evaluate_recovery_quorum(profile, verified)
        if evaluation.decision == "allow":
            attempt.status = RecoveryAttemptStatus.COOLDOWN.value
            self._audit("recovery_quorum_satisfied", pass_lookup_hash=attempt.pass_lookup_hash, metadata={"attempt_hash": attempt.attempt_hash, "verified_factors": verified})
        self.db.flush()
        self._audit("recovery_factor_verified", pass_lookup_hash=attempt.pass_lookup_hash, metadata={"attempt_hash": attempt.attempt_hash, "factor_type": factor.value})
        return RecoveryFactorResult(
            recovery_attempt_id=attempt.attempt_hash,
            status=attempt.status,
            verified_factors=verified,
            threshold=profile.threshold,
            decision=evaluation.decision,
            reason=evaluation.reason,
        )

    def evaluate_quorum(self, *, recovery_attempt_id: str) -> RecoveryStatusResult:
        attempt = self._get_attempt(recovery_attempt_id)
        profile = recovery_quorum_profile(
            (attempt.metadata_json or {}).get("declared_plan_code", PlanCode.LITE.value),
            cooldown_seconds=self.cooldown_seconds,
        )
        evaluation = evaluate_recovery_quorum(profile, _verified_factor_values(attempt.verified_factors_json))
        return RecoveryStatusResult(
            recovery_attempt_id=attempt.attempt_hash,
            status=attempt.status,
            threshold=profile.threshold,
            verified_factor_count=len(evaluation.verified_factors),
            missing_factor_count=max(profile.threshold - len(evaluation.verified_factors), 0),
            decision=evaluation.decision,
            reason=evaluation.reason,
            cooldown_until=attempt.cooldown_until,
        )

    def enforce_cooldown(self, attempt: RecoveryAttempt) -> None:
        cooldown_until = attempt.cooldown_until
        if cooldown_until and cooldown_until.tzinfo is None:
            cooldown_until = cooldown_until.replace(tzinfo=UTC)
        if cooldown_until and cooldown_until > datetime.now(UTC):
            raise RecoveryError("cooldown_required")

    def complete_recovery(self, *, recovery_attempt_id: str, new_device_public_key: str | None = None, new_device_key_fingerprint: str | None = None, revoke_old_sessions: bool = True) -> RecoveryCompleteResult:
        attempt = self._get_attempt(recovery_attempt_id)
        profile = recovery_quorum_profile((attempt.metadata_json or {}).get("declared_plan_code", PlanCode.LITE.value), cooldown_seconds=self.cooldown_seconds)
        evaluation = evaluate_recovery_quorum(profile, _verified_factor_values(attempt.verified_factors_json))
        policy_decision = self.policy.evaluate_completion(
            quorum=evaluation,
            cooldown_until=attempt.cooldown_until,
            failed_factor_count=attempt.failed_factor_count,
            issuer_policy_required=profile.plan_code == PlanCode.ENTERPRISE and profile.requires_policy_check,
            issuer_policy_satisfied=bool((attempt.metadata_json or {}).get("issuer_policy_satisfied")),
        )
        if not policy_decision.allowed:
            self._audit("recovery_denied", pass_lookup_hash=attempt.pass_lookup_hash, metadata={"attempt_hash": attempt.attempt_hash, "reason": policy_decision.reason})
            raise RecoveryError(policy_decision.decision)
        metadata = attempt.metadata_json or {}
        certificate_fingerprint = metadata.get("certificate_fingerprint")
        device_fingerprint = new_device_key_fingerprint or metadata.get("new_device_key_fingerprint")
        if new_device_public_key and device_fingerprint and certificate_fingerprint:
            self.db.add(AccessDevice(certificate_fingerprint=certificate_fingerprint, device_key_fingerprint=device_fingerprint, device_public_key=new_device_public_key, device_class="recovered", status="pending", first_seen_at=datetime.now(UTC), last_seen_at=datetime.now(UTC), risk_score=70, metadata_json={"recovery_attempt_hash": attempt.attempt_hash}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))
        old_sessions_revoked = 0
        if revoke_old_sessions and certificate_fingerprint:
            sessions = self.db.execute(select(AccessSession).where(AccessSession.certificate_fingerprint == certificate_fingerprint, AccessSession.status == "active")).scalars().all()
            for session in sessions:
                session.status = "revoked"
                session.revoked_at = datetime.now(UTC)
                old_sessions_revoked += 1
        attempt.status = RecoveryAttemptStatus.COMPLETED.value
        attempt.completed_at = datetime.now(UTC)
        attempt.updated_at = datetime.now(UTC)
        self.db.flush()
        self._audit("recovery_completed", pass_lookup_hash=attempt.pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, metadata={"attempt_hash": attempt.attempt_hash, "old_sessions_revoked": old_sessions_revoked})
        return RecoveryCompleteResult(attempt.attempt_hash, attempt.status, certificate_fingerprint, device_fingerprint, old_sessions_revoked, [RECOVERY_SAFETY_WARNING])

    def rotate_recovery(self, *, pass_lookup_hash: str, certificate_fingerprint: str | None, plan_code: PlanCode | str) -> RecoveryRotateResult:
        existing = self.db.execute(select(RecoveryQuorum).where(RecoveryQuorum.pass_lookup_hash == pass_lookup_hash, RecoveryQuorum.status == "active")).scalars().all()
        for quorum in existing:
            quorum.status = "rotated"
            quorum.rotated_at = datetime.now(UTC)
        result = self.setup_recovery(pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, plan_code=plan_code)
        self._audit("recovery_rotated", pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, metadata={"new_factor_id": result.recovery_factor_id})
        return result

    def cancel_recovery(self, *, recovery_attempt_id: str) -> RecoveryStatusResult:
        attempt = self._get_attempt(recovery_attempt_id)
        attempt.status = RecoveryAttemptStatus.CANCELLED.value
        attempt.cancelled_at = datetime.now(UTC)
        attempt.updated_at = datetime.now(UTC)
        self.db.flush()
        self._audit("recovery_cancelled", pass_lookup_hash=attempt.pass_lookup_hash, metadata={"attempt_hash": attempt.attempt_hash})
        return self.evaluate_quorum(recovery_attempt_id=recovery_attempt_id)

    def get_recovery_status(self, *, recovery_attempt_id: str) -> RecoveryStatusResult:
        return self.evaluate_quorum(recovery_attempt_id=recovery_attempt_id)

    def _verify_factor_value(self, quorum: RecoveryQuorum, factor: RecoveryFactorType, value: str) -> bool:
        reject_bitcoin_wallet_seed_warning(value)
        factors = [item for item in (quorum.factors_json or []) if isinstance(item, dict)]
        if factor in {RecoveryFactorType.RECOVERY_PHRASE_12, RecoveryFactorType.RECOVERY_PHRASE_24, RecoveryFactorType.BUSINESS_RECOVERY_SEED}:
            commitment = recovery_phrase_commitment(value, self.server_pepper)
            return any(item.get("factor_type") == factor.value and item.get("factor_commitment") == commitment and item.get("status") == "active" for item in factors)
        commitment = hmac_sha256_prefixed(self.server_pepper, f"recovery_factor:{factor.value}:{value}")
        return any(item.get("factor_type") == factor.value and item.get("factor_commitment") == commitment and item.get("status") == "active" for item in factors)

    def _get_or_create_quorum(self, pass_lookup_hash: str, certificate_fingerprint: str | None, plan: PlanCode) -> RecoveryQuorum:
        existing = self.db.execute(select(RecoveryQuorum).where(RecoveryQuorum.pass_lookup_hash == pass_lookup_hash, RecoveryQuorum.status == "active").order_by(RecoveryQuorum.id.desc())).scalars().first()
        if existing is not None:
            return existing
        profile = recovery_quorum_profile(plan, cooldown_seconds=self.cooldown_seconds)
        now = datetime.now(UTC)
        quorum = RecoveryQuorum(pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, quorum_type=f"{plan.value}_recovery", threshold_required=profile.threshold, total_factors=len(profile.allowed_factors), factors_json=[], status="active", policy_json={"allowed_factors": [factor.value for factor in profile.allowed_factors]}, created_at=now, updated_at=now)
        self.db.add(quorum)
        self.db.flush()
        return quorum

    def _get_attempt(self, attempt_hash: str) -> RecoveryAttempt:
        attempt = self.db.execute(select(RecoveryAttempt).where(RecoveryAttempt.attempt_hash == attempt_hash)).scalar_one_or_none()
        if attempt is None:
            raise RecoveryError("recovery_attempt_not_found")
        return attempt

    def _get_quorum(self, attempt: RecoveryAttempt) -> RecoveryQuorum:
        quorum = self.db.get(RecoveryQuorum, attempt.recovery_quorum_id) if attempt.recovery_quorum_id else None
        if quorum is None:
            raise RecoveryError("recovery_quorum_not_found")
        return quorum

    def _factor_failed(self, attempt: RecoveryAttempt, reason: str) -> None:
        attempt.failed_factor_count += 1
        attempt.updated_at = datetime.now(UTC)
        if attempt.failed_factor_count >= self.policy.max_attempts_per_hour:
            attempt.status = RecoveryAttemptStatus.LOCKED.value
        self.db.flush()
        self._audit("recovery_factor_failed", pass_lookup_hash=attempt.pass_lookup_hash, metadata={"attempt_hash": attempt.attempt_hash, "reason": reason})

    def _reject_revoked(self, pass_lookup_hash: str, certificate_fingerprint: str | None) -> None:
        result = self.revocations.check_access_material(self.db, pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint)
        if result.get("allowed") is False or result.get("revoked_targets"):
            raise RecoveryError("target_revoked")

    def _audit(self, event_type: str, **kwargs: Any) -> None:
        self.audit_chain.record_event(event_type=event_type, **kwargs)


def _strength_for_plan(plan: PlanCode) -> RecoveryPhraseStrength:
    if plan in {PlanCode.PRO, PlanCode.BUSINESS, PlanCode.ENTERPRISE}:
        return RecoveryPhraseStrength.WORDS_24
    return RecoveryPhraseStrength.WORDS_12


def _phrase_factor_for_plan(plan: PlanCode) -> RecoveryFactorType:
    if plan == PlanCode.BUSINESS:
        return RecoveryFactorType.BUSINESS_RECOVERY_SEED
    if plan in {PlanCode.PRO, PlanCode.ENTERPRISE}:
        return RecoveryFactorType.RECOVERY_PHRASE_24
    return RecoveryFactorType.RECOVERY_PHRASE_12


def _verified_factor_values(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def result_to_dict(result: Any) -> dict[str, Any]:
    return asdict(result)
