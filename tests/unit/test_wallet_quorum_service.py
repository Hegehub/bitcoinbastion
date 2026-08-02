from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.db.models.wallet_auth import MultiWalletQuorum
from app.domain.wallet_auth.quorum import (
    QuorumParticipantSlot,
    QuorumParticipantType as P,
    QuorumPolicy,
    QuorumProofMethod as M,
    QuorumStatus,
    QuorumType,
    VerifiedQuorumApproval,
)
from app.services.wallet_auth.quorum_service import QuorumError, WalletQuorumService

NOW = datetime(2099, 1, 1, tzinfo=UTC)


class Clock:
    now = NOW

    def __call__(self):
        return self.now


class Policy:
    allow = True
    calls: list[str]

    def __init__(self):
        self.calls = []

    def authorize_quorum(self, *, action, policy, evaluation):
        self.calls.append(action)
        return self.allow, "policy_allowed" if self.allow else "policy_denied"


class Revocations:
    values = {}

    def check_quorum_targets(self, **targets):
        return dict(self.values)


def policy(*, cooldown=0, action="business_owner_change"):
    return QuorumPolicy(
        "business-v1",
        1,
        QuorumType.BUSINESS,
        action,
        2,
        (
            QuorumParticipantSlot("owner", "business_owner"),
            QuorumParticipantSlot("admin", "business_admin"),
        ),
        2,
        2,
        frozenset({P.BITCOIN_WALLET_PRINCIPAL, P.LIGHTNING_WALLET_PRINCIPAL}),
        frozenset({M.BIP322, M.LNURL_AUTH}),
        required_roles=frozenset({"business_owner", "business_admin"}),
        cooldown_seconds=cooldown,
    )


def approval(
    current_policy,
    *,
    principal="hmac:owner",
    key="hmac:key-owner",
    method=M.BIP322,
    role="business_owner",
    participant=P.BITCOIN_WALLET_PRINCIPAL,
):
    return VerifiedQuorumApproval(
        f"sha256:approval:{principal}",
        participant,
        participant,
        principal,
        key,
        method,
        f"sha256:proof:{principal}",
        "high_assurance" if method is M.BIP322 else "standard",
        NOW.isoformat(),
        (NOW + timedelta(minutes=5)).isoformat(),
        "sha256:intent",
        current_policy.action,
        current_policy.policy_hash,
        role,
        f"sha256:device:{principal}",
        method is M.HARDWARE_WALLET,
    )


def fixture():
    engine = create_engine("sqlite:///:memory:")
    MultiWalletQuorum.__table__.create(engine)
    AccessAuditEvent.__table__.create(engine)
    db = Session(engine)
    clock, authorizer = Clock(), Policy()
    service = WalletQuorumService(
        db,
        server_pepper="test-quorum-pepper",
        policy_authorizer=authorizer,
        revocation_checker=Revocations(),
        clock=clock,
    )
    return db, clock, authorizer, service


def test_distinct_wallet_and_method_approvals_satisfy_and_consume_once() -> None:
    db, _clock, authorizer, service = fixture()
    current = policy()
    quorum_hash, initial = service.create(
        principal_hash="hmac:requester",
        policy=current,
        intent_hash="sha256:intent",
        active_pop_session=True,
        human_intent_verified=True,
    )
    assert initial.status is QuorumStatus.PENDING
    partial = service.submit_approval(quorum_hash=quorum_hash, approval=approval(current))
    assert partial.status is QuorumStatus.PARTIALLY_SATISFIED
    complete = service.submit_approval(
        quorum_hash=quorum_hash,
        approval=approval(
            current,
            principal="hmac:admin",
            key="hmac:key-admin",
            method=M.LNURL_AUTH,
            role="business_admin",
            participant=P.LIGHTNING_WALLET_PRINCIPAL,
        ),
    )
    assert complete.status is QuorumStatus.SATISFIED
    assert complete.distinct_principals == complete.distinct_methods == 2
    decision = service.authorize_and_consume(
        quorum_hash=quorum_hash, action="business_owner_change"
    )
    assert decision.decision.value == "allow"
    with pytest.raises(QuorumError, match="consumed"):
        service.authorize_and_consume(quorum_hash=quorum_hash, action="business_owner_change")
    assert authorizer.calls == ["quorum_create", "quorum_satisfy", "business_owner_change"]
    db.close()


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("principal", "hmac:owner", "duplicate_principal"),
        ("key", "hmac:key-owner", "duplicate_underlying_key"),
    ],
)
def test_duplicate_authority_cannot_count_twice(field, value, reason) -> None:
    db, _clock, _authorizer, service = fixture()
    current = policy()
    quorum_hash, _ = service.create(
        principal_hash="hmac:requester",
        policy=current,
        intent_hash="sha256:intent",
        active_pop_session=True,
        human_intent_verified=True,
    )
    service.submit_approval(quorum_hash=quorum_hash, approval=approval(current))
    values = {
        "principal": "hmac:admin",
        "key": "hmac:key-admin",
        "method": M.LNURL_AUTH,
        "role": "business_admin",
        field: value,
    }
    with pytest.raises(QuorumError, match=reason):
        service.submit_approval(quorum_hash=quorum_hash, approval=approval(current, **values))
    db.close()


def test_policy_revocation_expiry_and_cooldown_fail_closed() -> None:
    db, clock, authorizer, service = fixture()
    current = policy(cooldown=60)
    quorum_hash, _ = service.create(
        principal_hash="hmac:requester",
        policy=current,
        intent_hash="sha256:intent",
        active_pop_session=True,
        human_intent_verified=True,
    )
    service.submit_approval(quorum_hash=quorum_hash, approval=approval(current))
    service.submit_approval(
        quorum_hash=quorum_hash,
        approval=approval(
            current,
            principal="hmac:admin",
            key="hmac:key-admin",
            method=M.LNURL_AUTH,
            role="business_admin",
            participant=P.LIGHTNING_WALLET_PRINCIPAL,
        ),
    )
    with pytest.raises(QuorumError, match="cooldown"):
        service.authorize_and_consume(quorum_hash=quorum_hash, action=current.action)
    clock.now += timedelta(seconds=61)
    authorizer.allow = False
    with pytest.raises(QuorumError, match="policy_denied"):
        service.authorize_and_consume(quorum_hash=quorum_hash, action=current.action)
    db.close()


def test_lnurl_auth_cannot_approve_treasury_ownership_action() -> None:
    db, _clock, _authorizer, service = fixture()
    current = policy(action="treasury_policy_change")
    quorum_hash, _ = service.create(
        principal_hash="hmac:requester",
        policy=current,
        intent_hash="sha256:intent",
        active_pop_session=True,
        human_intent_verified=True,
    )
    with pytest.raises(QuorumError, match="proof_too_weak"):
        service.submit_approval(
            quorum_hash=quorum_hash,
            approval=approval(
                current,
                principal="hmac:lightning",
                key="hmac:lightning-key",
                method=M.LNURL_AUTH,
                role="business_owner",
                participant=P.LIGHTNING_WALLET_PRINCIPAL,
            ),
        )
    db.close()
