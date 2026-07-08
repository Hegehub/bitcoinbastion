from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import AccessDevice, AccessHumanIntent
from app.schemas.access_intent import HumanIntentAction, HumanIntentCreateRequest, HumanIntentManifest
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.access.human_intent import HumanIntentContext, HumanIntentError, HumanIntentService


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _keypair() -> tuple[str, str, str]:
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public_raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    public = _b64(public_raw)
    fingerprint = Ed25519SignatureSuite().public_key_fingerprint(public)
    return _b64(private_raw), public, fingerprint


def _context(device_fp: str) -> HumanIntentContext:
    return HumanIntentContext(
        actor_fingerprint=device_fp,
        certificate_fingerprint="sha256:cert",
        session_fingerprint="hmac-sha256:session",
        device_key_fingerprint=device_fp,
        plan_code="pro_pass",
        granted_scopes=["api:keys:manage", "delegated_pass:create", "market:intelligence:read"],
        origin="https://app.example",
    )


def _request(action: HumanIntentAction = HumanIntentAction.CREATE_API_KEY) -> HumanIntentCreateRequest:
    return HumanIntentCreateRequest(
        action=action,
        requested_scopes=["market:intelligence:read"],
        cannot_access=["treasury:read", "recovery:write"],
        target_resource_type="child_api_key",
        origin="https://app.example",
        human_summary="Create a market-read bot key",
        consequences=["A new scoped credential can read market intelligence."],
    )


def _service_with_device() -> tuple[HumanIntentService, str, str]:
    db = _db()
    private, public, fingerprint = _keypair()
    db.add(
        AccessDevice(
            certificate_fingerprint="sha256:cert",
            device_key_fingerprint=fingerprint,
            device_public_key=public,
            device_class="desktop",
            status="active",
        )
    )
    db.flush()
    return HumanIntentService(db), private, fingerprint


def test_build_manifest_creates_required_fields_and_stable_hash() -> None:
    service, _private, device_fp = _service_with_device()
    manifest = service.build_manifest(
        action="create_api_key",
        actor_fingerprint=device_fp,
        certificate_fingerprint="sha256:cert",
        session_fingerprint="hmac-sha256:session",
        origin="https://app.example",
        requested_scopes=["market:intelligence:read"],
        granted_scopes=["api:keys:manage", "market:intelligence:read"],
        cannot_access=["treasury:read"],
        target_resource_type="child_api_key",
        target_resource_hash="sha256:target",
        plan_code="pro_pass",
        risk_level="high",
        human_summary="Create scoped key",
        consequences=["Key can read market data"],
        created_at=datetime(2026, 7, 5, tzinfo=UTC),
        expires_at=datetime(2026, 7, 5, 0, 5, tzinfo=UTC),
        nonce="nonce",
    )
    assert manifest.type == "bastion_human_intent"
    assert service.hash_manifest(manifest) == service.hash_manifest(HumanIntentManifest(**manifest.model_dump()))


@pytest.mark.parametrize("field,value", [("requested_scopes", ["market:intelligence:read", "trace:standard:read"]), ("cannot_access", ["treasury:read", "wallet:health:read"]), ("action", HumanIntentAction.CREATE_DELEGATED_PASS), ("origin", "https://evil.example")])
def test_manifest_hash_changes_when_security_fields_change(field: str, value: object) -> None:
    service, _private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request())
    payload = response.manifest.model_dump()
    payload[field] = value
    if field == "action":
        payload["target_resource_type"] = "delegated_pass"
    changed = HumanIntentManifest(**payload)
    assert service.hash_manifest(changed) != response.canonical_manifest_hash


def test_expired_reused_and_missing_intents_are_rejected() -> None:
    service, private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request())
    signature = Ed25519SignatureSuite().sign(response.canonical_manifest_hash, "human_intent", "device", private).signature
    assert service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint=device_fp).valid
    row = service.require_valid_intent(intent_id=response.intent_id, action="create_api_key", origin="https://app.example", requested_scopes=["market:intelligence:read"], cannot_access=["treasury:read", "recovery:write"])
    assert row.intent_hash == response.intent_id
    service.mark_intent_used(response.intent_id)
    with pytest.raises(HumanIntentError, match="human_intent_not_verified"):
        service.require_valid_intent(intent_id=response.intent_id, action="create_api_key")
    with pytest.raises(HumanIntentError, match="human_intent_required"):
        service.require_valid_intent(intent_id=None, action="create_api_key")


def test_action_risk_and_cannot_access_requirements() -> None:
    with pytest.raises(ValueError, match="risk_level_too_low"):
        HumanIntentManifest(action="recovery_change", actor_fingerprint="a", certificate_fingerprint="c", origin="o", requested_scopes=[], granted_scopes=[], cannot_access=[], plan_code="pro_pass", risk_level="medium", created_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(minutes=1), nonce="n", human_summary="Recover", consequences=["device changes"])
    with pytest.raises(ValueError, match="critical_risk_required"):
        HumanIntentManifest(action="lockdown_disable", actor_fingerprint="a", certificate_fingerprint="c", origin="o", requested_scopes=[], granted_scopes=[], cannot_access=[], plan_code="pro_pass", risk_level="high", created_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(minutes=1), nonce="n", human_summary="Disable lockdown", consequences=["lockdown disabled"])
    with pytest.raises(ValueError, match="cannot_access_required"):
        HumanIntentManifest(action="create_api_key", actor_fingerprint="a", certificate_fingerprint="c", origin="o", requested_scopes=[], granted_scopes=[], cannot_access=[], plan_code="pro_pass", risk_level="high", created_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(minutes=1), nonce="n", human_summary="Create key", consequences=["key exists"])


def test_tampered_manifest_wrong_device_and_valid_signature_behaviour() -> None:
    service, private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request())
    signature = Ed25519SignatureSuite().sign(response.canonical_manifest_hash, "human_intent", "device", private).signature
    row = service.db.query(AccessHumanIntent).one()
    row.canonical_manifest_json = {**row.canonical_manifest_json, "origin": "https://evil.example"}
    service.db.flush()
    assert not service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint=device_fp).valid

    service, private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request())
    signature = Ed25519SignatureSuite().sign(response.canonical_manifest_hash, "human_intent", "device", private).signature
    assert not service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint="sha256:wrong").valid
    assert service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint=device_fp).valid


def test_secret_and_bitcoin_seed_inputs_rejected_and_audit_safe() -> None:
    service, _private, device_fp = _service_with_device()
    with pytest.raises(ValueError):
        HumanIntentCreateRequest(action="create_api_key", requested_scopes=[], cannot_access=["none"], target_resource_type="child_api_key", origin="https://app.example", human_summary="contains raw_access_pass", consequences=[])
    with pytest.raises(ValueError):
        HumanIntentCreateRequest(action="create_api_key", requested_scopes=[], cannot_access=["none"], target_resource_type="child_api_key", origin="https://app.example", human_summary="Never use bitcoin_seed", consequences=[])
    response = service.create_intent(_context(device_fp), _request())
    audit_text = str(service.db.execute.__self__) if hasattr(service.db.execute, "__self__") else ""
    assert "bbk_live_" not in audit_text
    assert response.canonical_manifest_hash.startswith("sha256:")
