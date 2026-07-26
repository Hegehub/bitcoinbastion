import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.db.models.wallet_auth import RecoveryCapsule as CapsuleRow, WalletPrincipal
from app.services.access.audit_chain import AccessAuditChain
from app.services.wallet_auth.recovery.capsule import RecoveryCapsuleService
from app.services.wallet_auth.recovery.factor_registry import RecoveryFactorRegistry
from app.services.wallet_auth.recovery.models import (
    RecoveryCapsuleStatus,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryProfile,
)
from app.services.wallet_auth.recovery.verifiers import (
    ExistingEvidenceFactorVerifier,
    payment_proof_evidence_check,
)


class Clock:
    now = datetime(2026, 7, 26, 12, tzinfo=UTC)

    def __call__(self):
        return self.now


class Policy:
    calls = 0

    def authorize(self, *, action, capsule):
        self.calls += 1
        return True, "policy_allowed"


class Revocations:
    def check(self, **kwargs):
        return {}


class Artifacts:
    called = False

    def secure_after_recovery(self, *, capsule):
        self.called = True
        return ("wallet_session", "child_api_key", "delegated_pass")


def proof_check(capsule, submission, context):
    return True, "standard", "verified"


def test_recovery_capsule_full_flow_cooldown_policy_revocation_and_no_reuse() -> None:
    engine = create_engine("sqlite:///:memory:")
    WalletPrincipal.__table__.create(engine)
    CapsuleRow.__table__.create(engine)
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db:
        principal = WalletPrincipal(
            principal_hash="hmac:principal",
            principal_type="bitcoin_wallet_principal",
            status="active",
            verification_strength="standard",
            primary_proof_method="bip322",
            policy_epoch=1,
            crypto_epoch=1,
            schema_epoch=1,
        )
        db.add(principal)
        db.flush()
        registry = RecoveryFactorRegistry()
        registry.register(
            ExistingEvidenceFactorVerifier(RecoveryFactorType.BIP322_WALLET_PROOF, proof_check)
        )
        registry.register(
            ExistingEvidenceFactorVerifier(
                RecoveryFactorType.PAYMENT_PROOF, payment_proof_evidence_check
            )
        )
        clock, policy, artifacts = Clock(), Policy(), Artifacts()
        service = RecoveryCapsuleService(
            db,
            server_pepper="test-pepper",
            factor_registry=registry,
            policy_authorizer=policy,
            revocation_resolver=Revocations(),
            artifact_manager=artifacts,
            audit_chain=AccessAuditChain(db),
            clock=clock,
        )
        capsule = service.create(
            principal_id=principal.id,
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            recovery_profile=RecoveryProfile.LITE_BASIC,
            recovery_reason="lost_device",
            requested_operations=("bind_replacement_device",),
        )
        assert capsule.status is RecoveryCapsuleStatus.AWAITING_FACTORS
        first = RecoveryFactorSubmission(
            RecoveryFactorType.BIP322_WALLET_PROOF, "hmac:bip", "sha256:bip", clock.now
        )
        capsule = asyncio.run(
            service.submit_factor(capsule_hash=capsule.capsule_hash, submission=first)
        )
        assert capsule.status is RecoveryCapsuleStatus.AWAITING_FACTORS
        payment = RecoveryFactorSubmission(
            RecoveryFactorType.PAYMENT_PROOF,
            "hmac:payment",
            "sha256:payment",
            clock.now,
            {
                "settlement_verified": True,
                "principal_hash": principal.principal_hash,
                "payment_proof_status": "active",
            },
        )
        capsule = asyncio.run(
            service.submit_factor(capsule_hash=capsule.capsule_hash, submission=payment)
        )
        assert capsule.status is RecoveryCapsuleStatus.COOLDOWN
        with pytest.raises(ValueError, match="cooldown"):
            service.complete(capsule_hash=capsule.capsule_hash)
        clock.now += timedelta(minutes=31)
        result = service.complete(capsule_hash=capsule.capsule_hash)
        assert result.session_mode == "recovery_only" and result.requires_fresh_step_up
        assert policy.calls >= 6 and artifacts.called
        with pytest.raises(ValueError):
            service.complete(capsule_hash=capsule.capsule_hash)
        events = [row.event_type for row in db.execute(select(AccessAuditEvent)).scalars()]
        assert "recovery_capsule_created" in events and "recovery_completed" in events
