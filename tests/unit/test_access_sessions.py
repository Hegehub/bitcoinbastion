from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessChallenge, AccessDevice, AccessSession, SubscriptionEntitlement
from app.domain.access.errors import (
    AccessCertificateExpiredError,
    AccessCertificateInactiveError,
    AccessCertificateNotFoundError,
    ChallengeAlreadyUsedError,
    ChallengeExpiredError,
    ChallengeOriginMismatchError,
    DeviceInactiveError,
    DeviceNotFoundError,
    EntitlementExpiredError,
    EntitlementInactiveError,
    EntitlementMissingError,
    InvalidChallengeSignatureError,
    MissingRequiredScopeError,
    SessionExpiredError,
    SessionFrozenError,
    SessionNotFoundError,
    SessionRevokedError,
    TargetRevokedError,
)
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, SIGNALS_ADVANCED_READ, SIGNALS_STANDARD_READ
from app.services.access.challenge_service import AccessChallengeService
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.access.session_service import AccessSessionService

PEPPER = "session-pepper-for-tests"


class FakeRevocationRegistry:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()

    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


@pytest.fixture()
def key_pair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest.fixture()
def audit_events() -> list[tuple[str, dict[str, object]]]:
    return []


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    AccessCertificate.__table__.create(bind=engine)
    SubscriptionEntitlement.__table__.create(bind=engine)
    AccessDevice.__table__.create(bind=engine)
    AccessChallenge.__table__.create(bind=engine)
    AccessSession.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


def _certificate(db: Session, *, status: str = "active", expires_at: datetime | None = None) -> AccessCertificate:
    now = datetime.now(UTC)
    cert = AccessCertificate(
        pass_lookup_hash="hmac-sha256:pass",
        pass_commitment="sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="plus_pass",
        status=status,
        device_key_fingerprint="sha256:device",
        issuer_key_id="issuer-key-1",
        crypto_epoch=1,
        scopes_json=[MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        issuer_signature_json={},
        issued_at=now,
        expires_at=expires_at or now + timedelta(days=30),
    )
    db.add(cert)
    db.flush()
    return cert


def _entitlement(db: Session, *, status: str = "active", valid_until: datetime | None = None) -> SubscriptionEntitlement:
    now = datetime.now(UTC)
    entitlement = SubscriptionEntitlement(
        pass_lookup_hash="hmac-sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="plus_pass",
        status=status,
        metric_entitlements_json={"groups": ["market.intelligence", "signals.standard"]},
        limits_json={"requests_per_minute": 120},
        scopes_json=[MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        issuer_signature_json={},
        valid_from=now - timedelta(minutes=1),
        valid_until=valid_until or now + timedelta(days=30),
    )
    db.add(entitlement)
    db.flush()
    return entitlement


def _device(db: Session, public_key: str, *, status: str = "active") -> AccessDevice:
    now = datetime.now(UTC)
    device = AccessDevice(
        certificate_fingerprint="sha256:cert",
        device_key_fingerprint="sha256:device",
        device_public_key=public_key,
        device_class="desktop_vault",
        status=status,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(device)
    db.flush()
    return device


def _ready(db: Session, public_key: str) -> None:
    _certificate(db)
    _entitlement(db)
    _device(db, public_key)


def _services(
    db: Session,
    audit_events: list[tuple[str, dict[str, object]]],
    *,
    revocation_registry: FakeRevocationRegistry | None = None,
) -> tuple[AccessChallengeService, AccessSessionService]:
    challenge_service = AccessChallengeService(db, challenge_ttl_seconds=300)
    session_service = AccessSessionService(
        db,
        challenge_service=challenge_service,
        server_pepper=PEPPER,
        session_ttl_seconds=900,
        revocation_registry=revocation_registry,
        audit_chain=lambda event_type, payload: audit_events.append((event_type, payload)),
    )
    return challenge_service, session_service


def _challenge_and_signature(
    db: Session,
    private_key: str,
    audit_events: list[tuple[str, dict[str, object]]],
    *,
    origin: str = "https://bitcoinbastion.com",
    scopes: list[str] | None = None,
) -> tuple[str, str]:
    challenge_service, _ = _services(db, audit_events)
    result = challenge_service.create_challenge(
        certificate_fingerprint="sha256:cert",
        origin=origin,
        requested_scopes=scopes or [MARKET_INTELLIGENCE_READ],
        device_key_fingerprint="sha256:device",
    )
    signature = Ed25519SignatureSuite().sign(result.challenge_hash, "access_challenge", "device-key", private_key).signature
    return result.challenge_id, signature


def _create_session(db: Session, private_key: str, audit_events: list[tuple[str, dict[str, object]]]) -> tuple[AccessSessionService, str]:
    challenge_id, signature = _challenge_and_signature(db, private_key, audit_events)
    _, session_service = _services(db, audit_events)
    result = session_service.create_session_from_challenge(
        certificate_fingerprint="sha256:cert",
        challenge_id=challenge_id,
        origin="https://bitcoinbastion.com",
        device_key_fingerprint="sha256:device",
        challenge_signature=signature,
    )
    return session_service, result.session_token


def test_valid_signed_challenge_creates_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    _, session_service = _services(db_session, audit_events)

    result = session_service.create_session_from_challenge(
        certificate_fingerprint="sha256:cert",
        challenge_id=challenge_id,
        origin="https://bitcoinbastion.com/path",
        device_key_fingerprint="sha256:device",
        challenge_signature=signature,
    )

    assert result.session_token
    assert result.session_hash_fingerprint.startswith("sha256:")
    assert result.requires_request_signing is True
    assert result.scopes == [MARKET_INTELLIGENCE_READ]


def test_session_token_returned_once_and_not_stored(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, token = _create_session(db_session, private_key, audit_events)

    stored = session_service.get_session_by_token(token)

    assert stored is not None
    assert stored.session_hash == hmac_sha256_prefixed(PEPPER, token)
    assert token not in stored.session_hash
    assert stored.session_hash != sha256_prefixed(token)


def test_expired_challenge_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    challenge = db_session.get(AccessChallenge, 1)
    assert challenge is not None
    challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.flush()
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(ChallengeExpiredError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_used_challenge_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    challenge = db_session.get(AccessChallenge, 1)
    assert challenge is not None
    challenge.status = "used"
    db_session.flush()
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(ChallengeAlreadyUsedError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_wrong_origin_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(ChallengeOriginMismatchError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="app://bastion-desktop",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_missing_certificate_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(AccessCertificateNotFoundError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:other",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_expired_certificate_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _certificate(db_session, expires_at=datetime.now(UTC) - timedelta(days=1))
    _entitlement(db_session)
    _device(db_session, public_key)
    challenge = AccessChallenge(
        challenge_hash="sha256:challenge",
        certificate_fingerprint="sha256:cert",
        device_key_fingerprint="sha256:device",
        origin="https://bitcoinbastion.com",
        requested_scopes_json=[MARKET_INTELLIGENCE_READ],
        server_nonce_hash="sha256:nonce",
        challenge_payload_hash="sha256:payload",
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    db_session.add(challenge)
    db_session.flush()
    signature = Ed25519SignatureSuite().sign("sha256:challenge", "access_challenge", "device-key", private_key).signature
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(AccessCertificateExpiredError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id="sha256:challenge",
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_inactive_certificate_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _certificate(db_session, status="revoked")
    _entitlement(db_session)
    _device(db_session, public_key)
    challenge = AccessChallenge(
        challenge_hash="sha256:challenge",
        certificate_fingerprint="sha256:cert",
        device_key_fingerprint="sha256:device",
        origin="https://bitcoinbastion.com",
        requested_scopes_json=[MARKET_INTELLIGENCE_READ],
        server_nonce_hash="sha256:nonce",
        challenge_payload_hash="sha256:payload",
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    db_session.add(challenge)
    db_session.flush()
    signature = Ed25519SignatureSuite().sign("sha256:challenge", "access_challenge", "device-key", private_key).signature
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(AccessCertificateInactiveError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id="sha256:challenge",
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_missing_or_inactive_device_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _certificate(db_session)
    _entitlement(db_session)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(DeviceNotFoundError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )

    _device(db_session, public_key, status="frozen")
    with pytest.raises(DeviceInactiveError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_missing_expired_or_inactive_entitlement_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _certificate(db_session)
    _device(db_session, public_key)
    _entitlement(db_session)
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    db_session.query(SubscriptionEntitlement).delete()
    db_session.flush()
    _, session_service = _services(db_session, audit_events)

    with pytest.raises(EntitlementMissingError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )

    _entitlement(db_session, valid_until=datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(EntitlementExpiredError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )

    db_session.query(SubscriptionEntitlement).delete()
    _entitlement(db_session, status="frozen")
    with pytest.raises(EntitlementInactiveError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_revoked_target_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    registry = FakeRevocationRegistry()
    registry.revoked.add(("device", "sha256:device"))
    challenge_id, signature = _challenge_and_signature(db_session, private_key, audit_events)
    _, session_service = _services(db_session, audit_events, revocation_registry=registry)

    with pytest.raises(TargetRevokedError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature=signature,
        )


def test_invalid_challenge_signature_cannot_create_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    _private_key, public_key = key_pair
    _ready(db_session, public_key)
    challenge_service, session_service = _services(db_session, audit_events)
    result = challenge_service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])

    with pytest.raises(InvalidChallengeSignatureError):
        session_service.create_session_from_challenge(
            certificate_fingerprint="sha256:cert",
            challenge_id=result.challenge_id,
            origin="https://bitcoinbastion.com",
            device_key_fingerprint="sha256:device",
            challenge_signature="invalid_signature",
        )


def test_valid_session_validates_and_updates_last_seen(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, token = _create_session(db_session, private_key, audit_events)

    context = session_service.validate_session(session_token=token, required_scopes=[MARKET_INTELLIGENCE_READ])
    stored = session_service.get_session_by_token(token)

    assert context.certificate_fingerprint == "sha256:cert"
    assert context.pass_lookup_hash == "hmac-sha256:pass"
    assert stored is not None
    assert stored.last_seen_at is not None


def test_session_validation_rejects_expired_revoked_frozen_and_missing_scope(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, token = _create_session(db_session, private_key, audit_events)
    stored = session_service.get_session_by_token(token)
    assert stored is not None

    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(SessionExpiredError):
        session_service.validate_session(session_token=token)

    stored.expires_at = datetime.now(UTC) + timedelta(minutes=5)
    stored.status = "revoked"
    with pytest.raises(SessionRevokedError):
        session_service.validate_session(session_token=token)

    stored.status = "frozen"
    with pytest.raises(SessionFrozenError):
        session_service.validate_session(session_token=token)

    stored.status = "active"
    with pytest.raises(MissingRequiredScopeError):
        session_service.validate_session(session_token=token, required_scopes=[SIGNALS_ADVANCED_READ])


def test_revoking_and_freezing_sessions_emit_audit(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, token = _create_session(db_session, private_key, audit_events)

    session_service.revoke_session(session_token=token, reason="operator_revoked")
    assert any(event == "session_revoked" for event, _ in audit_events)

    stored = session_service.get_session_by_token(token)
    assert stored is not None
    stored.status = "active"
    db_session.flush()
    frozen = session_service.freeze_sessions_for_certificate(certificate_fingerprint="sha256:cert", reason="lockdown")
    assert frozen == 1
    assert any(event == "session_frozen" for event, _ in audit_events)


def test_session_creation_emits_audit_without_raw_token(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]], caplog: pytest.LogCaptureFixture) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, token = _create_session(db_session, private_key, audit_events)

    assert any(event == "session_created" for event, _ in audit_events)
    assert token not in caplog.text
    assert all(token not in str(payload) for _, payload in audit_events)
    assert session_service.get_session_by_token("bbp_live_not_a_session") is None


def test_authorization_bearer_is_not_accepted_as_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    session_service, _token = _create_session(db_session, private_key, audit_events)

    with pytest.raises(SessionNotFoundError):
        session_service.validate_session(session_token="Bearer session_example_not_real")
