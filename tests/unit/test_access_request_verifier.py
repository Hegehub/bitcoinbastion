from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessDevice, AccessRequestNonce, AccessSession, SubscriptionEntitlement
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ
from app.services.access.crypto.hashing import body_hash, hmac_sha256_prefixed
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.access.request_verifier import (
    AccessRequestVerifier,
    ExpiredSessionError,
    InvalidBodyHashError,
    InvalidRequestSignatureError,
    InvalidSessionError,
    MissingAccessHeaderError,
    ReusedNonceError,
    RevokedSessionError,
    StaleTimestampError,
    UnsupportedSignatureSuiteError,
    build_request_digest,
)

PEPPER = "request-verifier-pepper"
SESSION_TOKEN = "session_example_not_real"
SESSION_HASH = hmac_sha256_prefixed(PEPPER, SESSION_TOKEN)
METHOD = "POST"
PATH = "/api/v1/private/metrics"
BODY = b'{"metric":"btc.price"}'


class FakeRevocationRegistry:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()

    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


class UnsupportedSuite:
    alg = "unsupported"

    def sign(self, *_args: object, **_kwargs: object) -> object:
        raise NotImplementedError

    def verify(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("unsupported suite")

    def public_key_fingerprint(self, *_args: object, **_kwargs: object) -> str:
        raise NotImplementedError


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
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    AccessCertificate.__table__.create(bind=engine)
    SubscriptionEntitlement.__table__.create(bind=engine)
    AccessDevice.__table__.create(bind=engine)
    AccessSession.__table__.create(bind=engine)
    AccessRequestNonce.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def audit_events() -> list[tuple[str, dict[str, object]]]:
    return []


def _ready(db: Session, public_key: str, *, session_status: str = "active", expires_at: datetime | None = None) -> None:
    now = datetime.now(UTC)
    cert = AccessCertificate(
        pass_lookup_hash="hmac-sha256:pass",
        pass_commitment="sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="plus_pass",
        status="active",
        device_key_fingerprint="sha256:device",
        issuer_key_id="issuer-key-1",
        crypto_epoch=1,
        scopes_json=[MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        issuer_signature_json={},
        issued_at=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(cert)
    db.flush()
    ent = SubscriptionEntitlement(
        pass_lookup_hash="hmac-sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="plus_pass",
        status="active",
        metric_entitlements_json={"groups": ["market.intelligence"]},
        limits_json={"requests_per_minute": 120},
        scopes_json=[MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        issuer_signature_json={},
        valid_from=now - timedelta(minutes=1),
        valid_until=now + timedelta(days=30),
    )
    db.add(ent)
    db.flush()
    device = AccessDevice(
        certificate_fingerprint="sha256:cert",
        device_key_fingerprint="sha256:device",
        device_public_key=public_key,
        device_class="desktop_vault",
        status="active",
    )
    db.add(device)
    db.flush()
    session = AccessSession(
        session_hash=SESSION_HASH,
        certificate_fingerprint="sha256:cert",
        device_key_fingerprint="sha256:device",
        entitlement_id=ent.id,
        challenge_hash="sha256:challenge",
        scopes_json=[MARKET_INTELLIGENCE_READ],
        policy_context_json={"requires_request_signing": True},
        status=session_status,
        risk_level="low",
        expires_at=expires_at or now + timedelta(minutes=15),
    )
    db.add(session)
    db.flush()


def _headers(private_key: str, *, body: bytes = BODY, nonce: str = "nonce-example", timestamp: str | None = None, path: str = PATH, method: str = METHOD) -> dict[str, str]:
    ts = timestamp or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    bh = body_hash(body)
    digest = build_request_digest(method, path, bh, ts, nonce)
    signature = Ed25519SignatureSuite().sign(digest, "access_session", "device-key", private_key).signature
    return {
        "X-Bastion-Session": SESSION_TOKEN,
        "X-Bastion-Timestamp": ts,
        "X-Bastion-Nonce": nonce,
        "X-Bastion-Body-Hash": bh,
        "X-Bastion-Signature": signature,
    }


def _verifier(audit_events: list[tuple[str, dict[str, object]]], *, registry: FakeRevocationRegistry | None = None, signature_suite: object | None = None) -> AccessRequestVerifier:
    return AccessRequestVerifier(
        server_pepper=PEPPER,
        audit_emitter=lambda event_type, payload: audit_events.append((event_type, payload)),
        revocation_registry=registry,
        signature_suite=signature_suite,  # type: ignore[arg-type]
    )


def test_valid_signed_request_passes(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)

    verified = _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key))

    assert verified.session_hash == SESSION_HASH
    assert verified.certificate_fingerprint == "sha256:cert"
    assert verified.device_key_fingerprint == "sha256:device"
    assert verified.scopes == [MARKET_INTELLIGENCE_READ]
    assert verified.verification_level == "proof_of_possession_request_signature"
    assert any(event == "access_request_verified" for event, _ in audit_events)


@pytest.mark.parametrize(
    "header",
    ["X-Bastion-Session", "X-Bastion-Timestamp", "X-Bastion-Nonce", "X-Bastion-Body-Hash", "X-Bastion-Signature"],
)
def test_missing_required_headers_fail(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]], header: str) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key)
    headers.pop(header)

    with pytest.raises(MissingAccessHeaderError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)


def test_stale_and_future_timestamp_fail(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    old = (datetime.now(UTC) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")

    with pytest.raises(StaleTimestampError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key, timestamp=old))
    with pytest.raises(StaleTimestampError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key, timestamp=future))


def test_body_tampering_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)

    with pytest.raises(InvalidBodyHashError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=b'{"tampered":true}', headers=_headers(private_key))


def test_reused_nonce_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key, nonce="repeat-nonce")
    verifier = _verifier(audit_events)

    verifier.verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)
    db_session.commit()

    with pytest.raises(ReusedNonceError):
        verifier.verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)


def test_invalid_signature_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key)
    headers["X-Bastion-Signature"] = "invalid_signature"

    with pytest.raises(InvalidRequestSignatureError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)


def test_expired_session_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key, expires_at=datetime.now(UTC) - timedelta(seconds=1))

    with pytest.raises(ExpiredSessionError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key))


def test_revoked_session_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key, session_status="revoked")

    with pytest.raises(RevokedSessionError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key))


def test_unknown_session_fails(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key)
    headers["X-Bastion-Session"] = "unknown-session"

    with pytest.raises(InvalidSessionError):
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)


def test_revocation_registry_denies_session(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    registry = FakeRevocationRegistry()
    registry.revoked.add(("session", SESSION_HASH))

    with pytest.raises(RevokedSessionError):
        _verifier(audit_events, registry=registry).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key))


def test_unsupported_signature_suite_fails_closed(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)

    with pytest.raises(UnsupportedSignatureSuiteError):
        _verifier(audit_events, signature_suite=UnsupportedSuite()).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=_headers(private_key))


def test_sensitive_values_are_not_logged_or_in_errors(db_session: Session, key_pair: tuple[str, str], audit_events: list[tuple[str, dict[str, object]]], caplog: pytest.LogCaptureFixture) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key, nonce="secret-nonce")
    headers["X-Bastion-Signature"] = "invalid_signature"

    with pytest.raises(InvalidRequestSignatureError) as exc_info:
        _verifier(audit_events).verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)

    rendered_audit = str(audit_events)
    assert SESSION_TOKEN not in str(exc_info.value)
    assert SESSION_TOKEN not in caplog.text
    assert SESSION_TOKEN not in rendered_audit
    assert headers["X-Bastion-Signature"] not in caplog.text
    assert headers["X-Bastion-Nonce"] not in rendered_audit
