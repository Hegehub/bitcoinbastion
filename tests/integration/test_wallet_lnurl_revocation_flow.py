from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessRevocation
from app.services.access.revocation_registry import RevocationRegistry


def test_principal_full_tree_blocks_session_child_certificate_and_emits_audit() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessRevocation.__table__.create(engine)
    events: list[tuple[str, dict[str, object]]] = []
    registry = RevocationRegistry(
        audit_emitter=lambda event, payload: events.append((event, payload))
    )
    with Session(engine) as db:
        registry.revoke_actor_tree(
            db,
            actor_type="lightning_wallet_principal",
            actor_hash="hmac:principal",
            reason="wallet_principal_compromised",
            descendants={
                "wallet_session": ("hmac:old-session",),
                "child_api_key": ("hmac:child",),
                "delegated_pass": ("hmac:delegated",),
                "access_certificate": ("sha256:certificate",),
                "offline_validity_pack": ("sha256:pack",),
            },
        )
        for kind, digest in (
            ("wallet_session", "hmac:old-session"),
            ("child_api_key", "hmac:child"),
            ("delegated_pass", "hmac:delegated"),
            ("access_certificate", "sha256:certificate"),
            ("offline_validity_pack", "sha256:pack"),
        ):
            assert registry.is_revoked(db, target_type=kind, target_hash=digest).revoked
        new_device = registry.resolve_revocation_status(
            db,
            target_type="wallet_device",
            target_hash="sha256:new-device",
            parent_targets=(("lightning_wallet_principal", "hmac:principal"),),
        )
        assert new_device.revoked
        assert any(event == "wallet_principal_revoked" for event, _ in events)
