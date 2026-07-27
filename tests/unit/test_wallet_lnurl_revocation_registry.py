from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessRevocation
from app.services.access.revocation_registry import (
    REVOCATION_TARGET_TYPES,
    RevocationRegistry,
)


def _db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    AccessRevocation.__table__.create(engine)
    return Session(engine)


def test_target_contract_and_direct_resolution() -> None:
    required = {
        "bitcoin_wallet_principal",
        "lightning_wallet_principal",
        "wallet_proof",
        "lnurl_auth_key",
        "lnurl_k1",
        "lnurl_pay_request",
        "lnurl_payment_proof",
        "lnurl_withdraw_request",
        "lightning_address",
        "wallet_recovery_capsule",
        "payregister_terminal",
    }
    assert required <= REVOCATION_TARGET_TYPES
    with _db() as db:
        registry = RevocationRegistry()
        registry.revoke_target(
            db,
            target_type="lnurl_auth_key",
            target_hash="hmac-sha256:key",
            reason="lnurl_linking_key_compromised",
        )
        resolution = registry.resolve_revocation_status(
            db, target_type="lnurl_auth_key", target_hash="hmac-sha256:key"
        )
        assert resolution.revoked and resolution.policy_effect == "deny"


def test_temporary_suspension_expires_and_reversal_is_append_only() -> None:
    now = datetime.now(UTC)
    with _db() as db:
        registry = RevocationRegistry()
        registry.revoke_target(
            db,
            target_type="wallet_device",
            target_hash="sha256:device",
            reason="device_lost",
            expires_at=now + timedelta(seconds=30),
        )
        assert registry.is_revoked(
            db, target_type="wallet_device", target_hash="sha256:device", at_time=now
        ).suspended
        assert not registry.is_revoked(
            db,
            target_type="wallet_device",
            target_hash="sha256:device",
            at_time=now + timedelta(minutes=1),
        ).revoked
        reversed_status = registry.reverse_revocation(
            db, target_type="wallet_device", target_hash="sha256:device"
        )
        assert not reversed_status.revoked
        assert len(db.execute(select(AccessRevocation)).scalars().all()) == 2


def test_full_tree_inheritance_and_independent_proof_revocation() -> None:
    with _db() as db:
        registry = RevocationRegistry()
        registry.revoke_actor_tree(
            db,
            actor_type="lightning_wallet_principal",
            actor_hash="hmac:principal",
            reason="wallet_principal_compromised",
            descendants={"wallet_session": ("hmac:session",), "child_api_key": ("hmac:child",)},
        )
        inherited = registry.resolve_revocation_status(
            db,
            target_type="access_certificate",
            target_hash="sha256:cert",
            parent_targets=(("lightning_wallet_principal", "hmac:principal"),),
        )
        assert inherited.revoked and inherited.inherited_from_parent
        assert registry.is_revoked(
            db, target_type="wallet_session", target_hash="hmac:session"
        ).revoked

        registry.revoke_target(
            db,
            target_type="wallet_proof",
            target_hash="sha256:proof",
            reason="wallet_proof_rotated",
        )
        assert not registry.is_revoked(
            db, target_type="bitcoin_wallet_principal", target_hash="hmac:other"
        ).revoked


def test_private_lookup_hash_is_peppered_and_metadata_is_redacted() -> None:
    first = RevocationRegistry.derive_private_target_hash(
        pepper="pepper-a", target_type="lnurl_k1", identifier="a" * 64
    )
    second = RevocationRegistry.derive_private_target_hash(
        pepper="pepper-b", target_type="lnurl_k1", identifier="a" * 64
    )
    assert first != second and "a" * 64 not in first
    with _db() as db:
        registry = RevocationRegistry()
        registry.revoke_target(
            db,
            target_type="lnurl_k1",
            target_hash=first,
            reason="lnurl_k1_reuse_detected",
            metadata={
                "raw_k1": "a" * 64,
                "signature": "secret-signature",
                "state": "replay_detected",
            },
        )
        row = db.execute(select(AccessRevocation)).scalar_one()
        assert "a" * 64 not in str(row.metadata_json) and "secret-signature" not in str(
            row.metadata_json
        )
