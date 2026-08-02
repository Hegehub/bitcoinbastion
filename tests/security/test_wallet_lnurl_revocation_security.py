from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessRevocation
from app.services.access.revocation_registry import RevocationRegistry


def test_revocation_audit_and_storage_never_include_lnurl_secrets() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessRevocation.__table__.create(engine)
    events: list[tuple[str, dict[str, object]]] = []
    raw_k1, raw_key, raw_address = "ab" * 32, "02" + "cd" * 32, "merchant@example.invalid"
    registry = RevocationRegistry(
        audit_emitter=lambda event, payload: events.append((event, payload))
    )
    with Session(engine) as db:
        target = registry.derive_private_target_hash(
            pepper="test-only-pepper", target_type="lnurl_k1", identifier=raw_k1
        )
        registry.revoke_target(
            db,
            target_type="lnurl_k1",
            target_hash=target,
            reason="lnurl_k1_reuse_detected",
            metadata={"raw_k1": raw_k1, "linking_key": raw_key, "wallet_address": raw_address},
        )
        material = str(db.execute(select(AccessRevocation)).scalar_one().metadata_json) + str(
            events
        )
        assert raw_k1 not in material and raw_key not in material and raw_address not in material


def test_authoritative_outage_fails_closed_for_critical_action() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessRevocation.__table__.create(engine)
    with Session(engine) as db:
        resolution = RevocationRegistry().resolve_revocation_status(
            db,
            target_type="lnurl_withdraw_request",
            target_hash="hmac:withdraw",
            critical=True,
            authoritative_available=False,
        )
        assert resolution.revoked and resolution.policy_effect == "deny"
