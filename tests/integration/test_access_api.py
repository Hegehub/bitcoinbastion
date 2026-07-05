from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import access as access_api
from app.db.base import Base
from app.db.models.access import AccessCertificate, AccessPaymentIntent, SubscriptionEntitlement
from app.domain.access.plans import PlanCode
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ
from app.main import app


class _CommitOnly:
    def commit(self) -> None: ...


@dataclass
class _Intent:
    id: int
    status: str
    provider: str | None
    payment_method: str
    amount_sats: int
    plan_code: str
    expires_at: datetime | None = None


class _PaymentService:
    def __init__(self) -> None:
        self.db = _CommitOnly()
        self.intents: dict[int, _Intent] = {}
        self.next_id = 1

    def create_payment_intent(self, plan_code: PlanCode, payment_method: str, amount_sats: int, metadata: dict[str, Any]) -> _Intent:
        intent = _Intent(self.next_id, "invoice_created", payment_method, payment_method, amount_sats, plan_code.value, datetime.now(UTC) + timedelta(minutes=15))
        self.intents[intent.id] = intent
        self.next_id += 1
        return intent

    def get_payment_intent(self, payment_intent_id: int) -> _Intent | None:
        return self.intents.get(payment_intent_id)


class _UnpaidIssuer:
    def issue_certificate_for_paid_intent(self, *_args: Any, **_kwargs: Any) -> Any:
        PaymentNotSettledError = type("PaymentNotSettledError", (RuntimeError,), {})
        raise PaymentNotSettledError("payment_not_settled")


class _PaidIssuer:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.issued = False

    def issue_certificate_for_paid_intent(self, payment_intent_id: int, **kwargs: Any) -> Any:
        if self.issued:
            CertificateAlreadyIssuedError = type("CertificateAlreadyIssuedError", (RuntimeError,), {})
            raise CertificateAlreadyIssuedError("certificate_already_issued")
        self.issued = True
        now = datetime.now(UTC)
        fingerprint = "sha256:cert-api"
        intent = self.db.get(AccessPaymentIntent, payment_intent_id)
        if intent is None:
            intent = AccessPaymentIntent(id=payment_intent_id, payment_method="manual", provider="manual", amount_sats=1, plan_code="plus_pass", status="paid")
            self.db.add(intent)
        intent.metadata_json = {"access_certificate_fingerprint": fingerprint}
        cert = AccessCertificate(
            pass_lookup_hash="hmac-sha256:pass-api",
            pass_commitment="sha256:commit-api",
            certificate_fingerprint=fingerprint,
            plan_code="plus_pass",
            status="active",
            device_key_fingerprint="sha256:device-api",
            issuer_key_id="issuer-test",
            crypto_epoch=1,
            hash_suite_json={},
            scopes_json=[MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ],
            public_keys_json={},
            issuer_signature_json={},
            issued_at=now,
            expires_at=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
        )
        self.db.add(cert)
        self.db.flush()
        return SimpleNamespace(
            raw_access_pass="bbp_live_test_pass_once",
            access_certificate={"certificate_fingerprint": fingerprint, "plan_code": "plus_pass"},
            certificate_fingerprint=fingerprint,
            save_warning="save once",
        )


class _EntitlementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def issue_entitlement(self, **kwargs: Any) -> SubscriptionEntitlement:
        now = datetime.now(UTC)
        entitlement = SubscriptionEntitlement(
            pass_lookup_hash=kwargs["pass_lookup_hash"],
            certificate_fingerprint=kwargs["certificate_fingerprint"],
            plan_code=kwargs["plan_code"],
            status="active",
            metric_entitlements_json={"groups": ["market.basic", "market.intelligence"]},
            limits_json={"requests_per_minute": 120, "daily_metric_credits": 50_000},
            scopes_json=[MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ],
            issuer_key_id="issuer-test",
            issuer_signature_json={},
            crypto_epoch=1,
            valid_from=kwargs["valid_from"],
            valid_until=kwargs["valid_until"],
            created_at=now,
            updated_at=now,
        )
        self.db.add(entitlement)
        self.db.flush()
        return entitlement


@dataclass
class _ChallengeResult:
    challenge_id: str
    challenge_hash: str
    challenge_payload: dict[str, Any]
    expires_at: datetime
    status: str


class _ChallengeService:
    def __init__(self) -> None:
        self.db = _CommitOnly()

    def create_challenge(self, *, certificate_fingerprint: str, origin: str, requested_scopes: list[str], device_key_fingerprint: str | None = None) -> _ChallengeResult:
        if "signals:advanced:read" in requested_scopes:
            raise RuntimeError("requested_scope_not_allowed")
        return _ChallengeResult(
            "challenge-1",
            "sha256:challenge-1",
            {"origin": origin, "requested_scopes": sorted(requested_scopes), "certificate_fingerprint": certificate_fingerprint},
            datetime.now(UTC) + timedelta(minutes=5),
            "pending",
        )


@dataclass
class _SessionResult:
    session_token: str
    session_hash_fingerprint: str
    certificate_fingerprint: str
    device_key_fingerprint: str
    plan_code: PlanCode
    scopes: list[str]
    expires_at: datetime
    policy_mode: str
    requires_request_signing: bool


class _SessionService:
    def __init__(self) -> None:
        self.db = _CommitOnly()
        self.used = False
        self.frozen = False

    def create_session_from_challenge(self, **kwargs: Any) -> _SessionResult:
        if self.used:
            raise RuntimeError("challenge_used")
        self.used = True
        return _SessionResult("session-token-once", "hmac-sha256:sess", kwargs["certificate_fingerprint"], kwargs["device_key_fingerprint"], PlanCode.PLUS, [MARKET_INTELLIGENCE_READ], datetime.now(UTC) + timedelta(minutes=15), "proof_of_possession", True)

    def freeze_sessions_for_certificate(self, *, certificate_fingerprint: str, reason: str) -> int:
        self.frozen = True
        return 1


@dataclass
class _Context:
    certificate_fingerprint: str = "sha256:cert-api"
    plan_code: str = "plus_pass"
    scopes: list[str] = None  # type: ignore[assignment]
    expires_at: datetime = datetime.now(UTC) + timedelta(minutes=15)
    requires_request_signing: bool = True
    risk_level: str = "low"
    entitlement_id: int | None = None

    def __post_init__(self) -> None:
        if self.scopes is None:
            self.scopes = [MARKET_INTELLIGENCE_READ]


engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def _db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _override_db(db: Session):
    def _dependency():
        yield db

    return _dependency


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def _client() -> TestClient:
    app.dependency_overrides[access_api.get_db] = _db
    return TestClient(app)


def test_create_payment_intent() -> None:
    service = _PaymentService()
    app.dependency_overrides[access_api.get_payment_intent_service] = lambda: service
    response = _client().post("/api/v1/access/payment-intents", json={"plan_code": "lite_pass", "payment_method": "manual", "amount_sats": 1000})
    assert response.status_code == 201
    body = response.json()
    assert body["payment_intent_id"] == 1
    assert body["certificate_available"] is False


def test_unpaid_payment_cannot_issue_certificate() -> None:
    app.dependency_overrides[access_api.get_certificate_issuer] = lambda: _UnpaidIssuer()
    app.dependency_overrides[access_api.get_entitlement_service] = lambda: _EntitlementService(TestingSessionLocal())
    response = _client().post("/api/v1/access/certificates", json={"payment_intent_id": 1, "device_public_key": "pub"})
    assert response.status_code == 402


def test_paid_payment_issues_certificate_once() -> None:
    db = TestingSessionLocal()
    issuer = _PaidIssuer(db)
    app.dependency_overrides[access_api.get_db] = _override_db(db)
    app.dependency_overrides[access_api.get_certificate_issuer] = lambda: issuer
    app.dependency_overrides[access_api.get_entitlement_service] = lambda: _EntitlementService(db)
    client = TestClient(app)
    payload = {"payment_intent_id": 1, "device_public_key": "pub", "device_key_fingerprint": "sha256:device-api"}
    first = client.post("/api/v1/access/certificates", json=payload)
    second = client.post("/api/v1/access/certificates", json=payload)
    assert first.status_code == 200
    assert first.json()["raw_access_pass"] == "bbp_live_test_pass_once"
    assert second.status_code == 200
    assert second.json()["raw_access_pass"] is None


def test_create_challenge_for_valid_pass() -> None:
    app.dependency_overrides[access_api.get_challenge_service] = lambda: _ChallengeService()
    response = _client().post("/api/v1/access/challenges", json={"certificate_fingerprint": "sha256:cert-api", "origin": "https://bitcoinbastion.com", "requested_scopes": [MARKET_INTELLIGENCE_READ]})
    assert response.status_code == 200
    assert response.json()["challenge_payload"]["origin"] == "https://bitcoinbastion.com"


def test_challenge_rejects_scope_escalation() -> None:
    app.dependency_overrides[access_api.get_challenge_service] = lambda: _ChallengeService()
    response = _client().post("/api/v1/access/challenges", json={"certificate_fingerprint": "sha256:cert-api", "origin": "https://bitcoinbastion.com", "requested_scopes": ["signals:advanced:read"]})
    assert response.status_code == 403


def test_create_session_from_signed_challenge_and_reused_challenge_rejected() -> None:
    service = _SessionService()
    app.dependency_overrides[access_api.get_session_service] = lambda: service
    payload = {"challenge_id": "challenge-1", "certificate_fingerprint": "sha256:cert-api", "origin": "https://bitcoinbastion.com", "device_key_fingerprint": "sha256:device-api", "challenge_signature": "sig"}
    first = _client().post("/api/v1/access/sessions", json=payload)
    second = _client().post("/api/v1/access/sessions", json=payload)
    assert first.status_code == 200
    assert first.json()["session_token"] == "session-token-once"
    assert second.status_code == 403


def test_access_me_requires_session() -> None:
    response = _client().get("/api/v1/access/me")
    assert response.status_code == 401


def test_access_me_with_session() -> None:
    app.dependency_overrides[access_api.get_access_session_context] = lambda: _Context()
    response = _client().get("/api/v1/access/me", headers={"X-Bastion-Session": "session"})
    assert response.status_code == 200
    assert response.json()["plan_code"] == "plus_pass"


def test_entitlements_and_limits_endpoints() -> None:
    app.dependency_overrides[access_api.get_access_session_context] = lambda: _Context(entitlement_id=1)
    db = TestingSessionLocal()
    now = datetime.now(UTC)
    db.add(SubscriptionEntitlement(id=1, pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint="sha256:cert-api", plan_code="plus_pass", status="active", metric_entitlements_json={"groups": ["market.basic"]}, limits_json={"requests_per_minute": 120}, scopes_json=[MARKET_INTELLIGENCE_READ], issuer_signature_json={}, crypto_epoch=1, valid_from=now, valid_until=now + timedelta(days=1), created_at=now, updated_at=now))
    db.commit()
    app.dependency_overrides[access_api.get_db] = _override_db(db)
    client = TestClient(app)
    assert client.get("/api/v1/access/me/entitlements", headers={"X-Bastion-Session": "session"}).status_code == 200
    limits = client.get("/api/v1/access/me/limits", headers={"X-Bastion-Session": "session"})
    assert limits.status_code == 200
    assert limits.json()["limits"]["requests_per_minute"] == 120


def test_lockdown_freezes_session() -> None:
    service = _SessionService()
    app.dependency_overrides[access_api.get_access_session_context] = lambda: _Context()
    app.dependency_overrides[access_api.get_session_service] = lambda: service
    response = _client().post("/api/v1/access/lockdown", headers={"X-Bastion-Session": "session"})
    assert response.status_code == 200
    assert response.json()["frozen_sessions"] == 1
    assert service.frozen is True


def test_openapi_contains_access_routes() -> None:
    paths = _client().get("/openapi.json").json()["paths"]
    assert "/api/v1/access/payment-intents" in paths
    assert "/api/v1/access/certificates" in paths
    assert "/api/v1/access/challenges" in paths
    assert "/api/v1/access/sessions" in paths
    assert "/api/v1/access/me" in paths
