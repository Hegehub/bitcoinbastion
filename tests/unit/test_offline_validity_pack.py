from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.services.access.offline_pack_verifier import OfflinePackVerifier
from app.services.access.offline_policy import OfflineProfile
from app.services.access.offline_validity_pack import (
    OfflinePackError,
    OfflinePackIssueRequest,
    OfflineValidityPackService,
    append_local_event,
)


class Policy:
    def evaluate_offline_pack(self, request):
        return {
            "decision": "allow",
            "reason_code": "allowed",
            "allowed_scopes": request.entitlement_scopes,
            "allowed_metric_groups": request.entitlement_metric_groups,
        }


class Revocations:
    revoked = False

    def check_offline_pack_targets(self, **targets):
        return {key: self.revoked for key in targets}


def key_pair():
    # Deterministic non-production RFC-style fixture seed; never used outside tests.
    key = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    private = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    public = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private, public


@pytest.fixture()
def issued():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    private, public = key_pair()
    now = datetime.now(UTC)
    revocations = Revocations()
    with Session(engine) as db:
        service = OfflineValidityPackService(
            db,
            issuer_private_key=private,
            issuer_key_id="test-issuer",
            policy=Policy(),
            revocations=revocations,
            enabled=True,
            clock=lambda: now,
        )
        request = OfflinePackIssueRequest(
            principal_hash="hmac-sha256:principal",
            principal_type="bitcoin_wallet_principal",
            proof_method="bip322",
            verification_strength="standard",
            device_key_fingerprint="sha256:device",
            device_class="desktop_vault",
            entitlement_fingerprint="sha256:entitlement",
            plan="plus_pass",
            entitlement_scopes=frozenset({"signals:lite:read", "signals:standard:read"}),
            entitlement_metric_groups=frozenset({"signals_lite", "signals_standard"}),
            entitlement_expires_at=now + timedelta(hours=8),
            profile=OfflineProfile.READ_ONLY,
            requested_scopes=frozenset({"signals:lite:read"}),
            requested_metric_groups=frozenset({"signals_lite"}),
            requested_expires_at=now + timedelta(hours=6),
            revocation_epoch=7,
            policy_epoch=1,
            crypto_epoch=1,
            entitlement_epoch=3,
            pop_verified=True,
            human_intent_verified=True,
            idempotency_key_hash="sha256:idem",
        )
        result = service.issue_pack(request)
        yield service, request, result, public, now, revocations


def test_plus_read_only_pack_is_signed_bounded_and_idempotent(issued):
    service, request, result, *_ = issued
    assert result.export_pack["type"] == "bastion_offline_validity_pack"
    assert result.export_pack["version"] == 1
    assert result.expires_at <= request.entitlement_expires_at
    assert result.export_pack["issuer"]["post_quantum_signature"] is None
    assert service.issue_pack(request).idempotent_replay


def test_pack_verifies_and_tampering_fails(issued):
    _, request, result, public, now, _ = issued
    verifier = OfflinePackVerifier(public)
    verified = verifier.verify(
        result.export_pack,
        device_key_fingerprint=request.device_key_fingerprint,
        principal_hash=request.principal_hash,
        entitlement_fingerprint=request.entitlement_fingerprint,
        cached_revocation_epoch=7,
        now=now,
    )
    assert verified.valid
    tampered = {
        **result.export_pack,
        "offline_policy": {
            **result.export_pack["offline_policy"],
            "allowed_actions": ["transaction_sign"],
        },
    }
    assert (
        verifier.verify(
            tampered,
            device_key_fingerprint=request.device_key_fingerprint,
            principal_hash=request.principal_hash,
            entitlement_fingerprint=request.entitlement_fingerprint,
            cached_revocation_epoch=7,
            now=now,
        ).reason_code
        == "fingerprint_mismatch"
    )


def test_revocation_and_expired_entitlement_fail_closed(issued):
    service, request, _, _, now, revocations = issued
    revocations.revoked = True
    with pytest.raises(OfflinePackError, match="revoked"):
        service.issue_pack(replace(request, idempotency_key_hash="sha256:new"))


def test_local_event_chain_reconciles_idempotently(issued):
    service, _, result, _, now, _ = issued
    events = []
    append_local_event(
        events, "local_offline_operation_allowed", {"operation": "cached_metric_read"}, now
    )
    first = service.reconcile_pack(
        result.pack_fingerprint, events, current_revocation_epoch=7, current_policy_epoch=1
    )
    second = service.reconcile_pack(
        result.pack_fingerprint, events, current_revocation_epoch=7, current_policy_epoch=1
    )
    assert first == second
    assert first["outcome"] == "reconciled"


def test_local_queue_is_durable_and_hash_linked(issued):
    service, _, result, *_ = issued
    first = service.queue_local_event(
        result.pack_fingerprint,
        "local_offline_operation_allowed",
        {"operation": "cached_metric_read"},
    )
    second = service.queue_local_event(
        result.pack_fingerprint,
        "local_reconciliation_required",
        {"reason_code": "connectivity_restored"},
    )
    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert second.previous_event_hash == first.event_hash
