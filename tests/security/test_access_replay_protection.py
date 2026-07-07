from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import (
    AccessCertificate,
    AccessDevice,
    AccessRequestNonce,
    AccessSession,
    SubscriptionEntitlement,
)
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ
from app.services.access.crypto.hashing import body_hash, hmac_sha256_prefixed
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.access.request_verifier import (
    AccessRequestVerifier,
    InvalidBodyHashError,
    InvalidRequestSignatureError,
    ReusedNonceError,
    StaleTimestampError,
    build_request_digest,
)

PEPPER = "test-replay-pepper"
SESSION_TOKEN = "sess_test_replay_only"
SESSION_HASH = hmac_sha256_prefixed(PEPPER, SESSION_TOKEN)
METHOD = "POST"
PATH = "/api/v1/trace/business/report"
BODY = b'{"address":"bc1qtest"}'


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
    for table in (
        AccessCertificate.__table__,
        SubscriptionEntitlement.__table__,
        AccessDevice.__table__,
        AccessSession.__table__,
        AccessRequestNonce.__table__,
    ):
        table.create(bind=engine)
    with Session(engine) as session:
        yield session


def _ready(db: Session, public_key: str) -> None:
    now = datetime.now(UTC)
    cert = AccessCertificate(
        pass_lookup_hash="hmac-sha256:pass",
        pass_commitment="sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="business_pass",
        status="active",
        device_key_fingerprint="sha256:device",
        issuer_key_id="issuer-test",
        crypto_epoch=1,
        scopes_json=[MARKET_INTELLIGENCE_READ],
        issuer_signature_json={},
        issued_at=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(cert)
    db.flush()
    entitlement = SubscriptionEntitlement(
        pass_lookup_hash="hmac-sha256:pass",
        certificate_fingerprint="sha256:cert",
        plan_code="business_pass",
        status="active",
        metric_entitlements_json={"groups": ["market.intelligence"]},
        limits_json={"requests_per_minute": 120},
        scopes_json=[MARKET_INTELLIGENCE_READ],
        issuer_signature_json={},
        valid_from=now - timedelta(minutes=1),
        valid_until=now + timedelta(days=30),
    )
    db.add(entitlement)
    db.flush()
    db.add(
        AccessDevice(
            certificate_fingerprint="sha256:cert",
            device_key_fingerprint="sha256:device",
            device_public_key=public_key,
            device_class="desktop_vault",
            status="active",
        )
    )
    db.add(
        AccessSession(
            session_hash=SESSION_HASH,
            certificate_fingerprint="sha256:cert",
            device_key_fingerprint="sha256:device",
            entitlement_id=entitlement.id,
            challenge_hash="sha256:challenge",
            scopes_json=[MARKET_INTELLIGENCE_READ],
            policy_context_json={"requires_request_signing": True},
            status="active",
            risk_level="low",
            expires_at=now + timedelta(minutes=15),
        )
    )
    db.flush()


def _headers(
    private_key: str,
    *,
    method: str = METHOD,
    path: str = PATH,
    body: bytes = BODY,
    nonce: str = "nonce-1",
    timestamp: str | None = None,
) -> dict[str, str]:
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


def _verifier() -> AccessRequestVerifier:
    return AccessRequestVerifier(server_pepper=PEPPER, max_skew_seconds=120)


def test_same_nonce_is_rejected_after_first_valid_request(
    db_session: Session, key_pair: tuple[str, str]
) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    headers = _headers(private_key, nonce="replay-nonce")

    first = _verifier().verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)
    db_session.commit()

    assert first.session_hash == SESSION_HASH
    assert db_session.execute(select(AccessRequestNonce)).scalars().first() is not None
    with pytest.raises(ReusedNonceError):
        _verifier().verify(db_session, method=METHOD, path=PATH, body=BODY, headers=headers)


@pytest.mark.parametrize("offset", [-600, 600])
def test_stale_or_future_timestamp_fails(
    db_session: Session, key_pair: tuple[str, str], offset: int
) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)
    timestamp = (datetime.now(UTC) + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z")

    with pytest.raises(StaleTimestampError):
        _verifier().verify(
            db_session,
            method=METHOD,
            path=PATH,
            body=BODY,
            headers=_headers(private_key, timestamp=timestamp),
        )


def test_body_hash_mismatch_fails(db_session: Session, key_pair: tuple[str, str]) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)

    with pytest.raises(InvalidBodyHashError):
        _verifier().verify(
            db_session,
            method=METHOD,
            path=PATH,
            body=b'{"address":"tampered"}',
            headers=_headers(private_key),
        )


@pytest.mark.parametrize(("method", "path"), [("GET", PATH), (METHOD, "/api/v1/trace/enterprise/report")])
def test_changed_method_or_path_with_reused_signature_fails(
    db_session: Session, key_pair: tuple[str, str], method: str, path: str
) -> None:
    private_key, public_key = key_pair
    _ready(db_session, public_key)

    with pytest.raises(InvalidRequestSignatureError):
        _verifier().verify(
            db_session,
            method=method,
            path=path,
            body=BODY,
            headers=_headers(private_key, method=METHOD, path=PATH),
        )
