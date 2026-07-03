from __future__ import annotations

from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessChallenge, SubscriptionEntitlement
from app.domain.access.errors import (
    AccessCertificateInactiveError,
    ChallengeAlreadyUsedError,
    ChallengeExpiredError,
    ChallengeRevokedError,
    InvalidOriginError,
    OriginRequiredError,
    RequestedScopeNotAllowedError,
    SubscriptionEntitlementInactiveError,
    UnknownScopeError,
    UnsafeScopeError,
)
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, SIGNALS_ADVANCED_READ, SIGNALS_STANDARD_READ
from app.services.access.challenge_service import AccessChallengeService, CHALLENGE_STATUS_REVOKED


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    AccessCertificate.__table__.create(bind=engine)
    SubscriptionEntitlement.__table__.create(bind=engine)
    AccessChallenge.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def service(db_session: Session) -> AccessChallengeService:
    return AccessChallengeService(db_session, challenge_ttl_seconds=300)


def _certificate(db: Session, *, status: str = "active", fingerprint: str = "sha256:cert") -> AccessCertificate:
    now = datetime.now(UTC)
    cert = AccessCertificate(
        pass_lookup_hash="hmac-sha256:pass",
        pass_commitment="sha256:pass",
        certificate_fingerprint=fingerprint,
        plan_code="plus_pass",
        status=status,
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
    return cert


def _entitlement(db: Session, *, status: str = "active", scopes: list[str] | None = None, cert_fp: str = "sha256:cert") -> SubscriptionEntitlement:
    now = datetime.now(UTC)
    ent = SubscriptionEntitlement(
        pass_lookup_hash="hmac-sha256:pass",
        certificate_fingerprint=cert_fp,
        plan_code="plus_pass",
        status=status,
        metric_entitlements_json={"groups": ["market.intelligence", "signals.standard"]},
        limits_json={"requests_per_minute": 120},
        scopes_json=scopes or [MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        issuer_signature_json={},
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )
    db.add(ent)
    db.flush()
    return ent


def _ready(db: Session) -> None:
    _certificate(db)
    _entitlement(db)


def test_creates_valid_challenge(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)

    result = service.create_challenge(
        certificate_fingerprint="sha256:cert",
        origin="https://BitcoinBastion.com/path?ignored=true",
        requested_scopes=[SIGNALS_STANDARD_READ, MARKET_INTELLIGENCE_READ],
        device_key_fingerprint="sha256:device",
    )

    assert result.challenge_hash.startswith("sha256:")
    assert result.expires_at > datetime.now(UTC)
    assert result.challenge_payload["origin"] == "https://bitcoinbastion.com"
    assert result.challenge_payload["requested_scopes"] == sorted([MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ])
    assert result.challenge_payload["challenge_hash"] == result.challenge_hash
    assert "server_nonce" in result.challenge_payload


def test_rejects_unknown_scope(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)

    with pytest.raises(UnknownScopeError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=["unknown:scope"])


def test_rejects_scope_escalation(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)

    with pytest.raises(RequestedScopeNotAllowedError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[SIGNALS_ADVANCED_READ])


@pytest.mark.parametrize("scope", ["api:all", "metrics:all", "admin:all"])
def test_rejects_unsafe_broad_scope(service: AccessChallengeService, db_session: Session, scope: str) -> None:
    _ready(db_session)

    with pytest.raises(UnsafeScopeError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[scope])


def test_rejects_missing_origin(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)

    with pytest.raises(OriginRequiredError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="", requested_scopes=[MARKET_INTELLIGENCE_READ])


@pytest.mark.parametrize("origin", ["http://bitcoinbastion.com", "not-a-url", "ftp://bitcoinbastion.com"])
def test_rejects_invalid_origin(service: AccessChallengeService, db_session: Session, origin: str) -> None:
    _ready(db_session)

    with pytest.raises(InvalidOriginError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin=origin, requested_scopes=[MARKET_INTELLIGENCE_READ])


def test_challenge_hash_is_stable_for_same_input(service: AccessChallengeService) -> None:
    issued = datetime(2026, 7, 2, tzinfo=UTC)
    expires = issued + timedelta(minutes=5)

    first = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="https://bitcoinbastion.com",
        requested_scopes=[SIGNALS_STANDARD_READ, MARKET_INTELLIGENCE_READ],
        server_nonce="nonce",
        issued_at=issued,
        expires_at=expires,
    )
    second = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="https://bitcoinbastion.com/ignored",
        requested_scopes=[MARKET_INTELLIGENCE_READ, SIGNALS_STANDARD_READ],
        server_nonce="nonce",
        issued_at=issued,
        expires_at=expires,
    )

    assert first["challenge_hash"] == second["challenge_hash"]


def test_challenge_hash_changes_with_origin(service: AccessChallengeService) -> None:
    issued = datetime(2026, 7, 2, tzinfo=UTC)
    expires = issued + timedelta(minutes=5)
    first = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="https://bitcoinbastion.com",
        requested_scopes=[MARKET_INTELLIGENCE_READ],
        server_nonce="nonce",
        issued_at=issued,
        expires_at=expires,
    )
    second = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="app://bastion-desktop",
        requested_scopes=[MARKET_INTELLIGENCE_READ],
        server_nonce="nonce",
        issued_at=issued,
        expires_at=expires,
    )

    assert first["challenge_hash"] != second["challenge_hash"]


def test_challenge_hash_changes_with_nonce(service: AccessChallengeService) -> None:
    issued = datetime(2026, 7, 2, tzinfo=UTC)
    expires = issued + timedelta(minutes=5)
    first = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="https://bitcoinbastion.com",
        requested_scopes=[MARKET_INTELLIGENCE_READ],
        server_nonce="nonce-1",
        issued_at=issued,
        expires_at=expires,
    )
    second = service.build_challenge_payload(
        certificate_fingerprint="sha256:cert",
        origin="https://bitcoinbastion.com",
        requested_scopes=[MARKET_INTELLIGENCE_READ],
        server_nonce="nonce-2",
        issued_at=issued,
        expires_at=expires,
    )

    assert first["challenge_hash"] != second["challenge_hash"]


def test_expired_challenge_rejected(db_session: Session) -> None:
    _ready(db_session)
    service = AccessChallengeService(db_session, challenge_ttl_seconds=30)
    result = service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])
    challenge = service.verify_challenge_exists(result.challenge_id)
    challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.flush()

    with pytest.raises(ChallengeExpiredError):
        service.mark_challenge_used(result.challenge_id)


def test_used_challenge_rejected(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)
    result = service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])

    service.mark_challenge_used(result.challenge_id, origin="https://bitcoinbastion.com")

    with pytest.raises(ChallengeAlreadyUsedError):
        service.mark_challenge_used(result.challenge_id, origin="https://bitcoinbastion.com")


def test_revoked_challenge_rejected(service: AccessChallengeService, db_session: Session) -> None:
    _ready(db_session)
    result = service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])
    challenge = service.verify_challenge_exists(result.challenge_id)
    challenge.status = CHALLENGE_STATUS_REVOKED
    db_session.flush()

    with pytest.raises(ChallengeRevokedError):
        service.mark_challenge_used(result.challenge_id)


def test_no_secret_leakage(service: AccessChallengeService, db_session: Session, caplog: pytest.LogCaptureFixture) -> None:
    _ready(db_session)
    raw_pass = "bbp_live_secret_example"

    result = service.create_challenge(certificate_fingerprint="sha256:cert", origin="cli://bastion-cli", requested_scopes=[MARKET_INTELLIGENCE_READ])

    assert raw_pass not in str(result.challenge_payload)
    assert raw_pass not in caplog.text
    assert result.challenge_payload["server_nonce"] not in caplog.text
    assert "bitcoin_seed" not in str(result.challenge_payload).lower()
    assert "private_key" not in str(result.challenge_payload).lower()


def test_certificate_inactive_rejected(service: AccessChallengeService, db_session: Session) -> None:
    _certificate(db_session, status="revoked")
    _entitlement(db_session)

    with pytest.raises(AccessCertificateInactiveError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])


def test_entitlement_inactive_rejected(service: AccessChallengeService, db_session: Session) -> None:
    _certificate(db_session)
    _entitlement(db_session, status="revoked")

    with pytest.raises(SubscriptionEntitlementInactiveError):
        service.create_challenge(certificate_fingerprint="sha256:cert", origin="https://bitcoinbastion.com", requested_scopes=[MARKET_INTELLIGENCE_READ])
