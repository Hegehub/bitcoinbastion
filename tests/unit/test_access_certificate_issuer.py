from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessPaymentIntent
from app.domain.access.entitlements import get_plan_scopes
from app.domain.access.plans import PlanCode
from app.domain.access.scopes import FORBIDDEN_SCOPES, SIGNALS_ADVANCED_READ
from app.services.access.certificate_issuer import (
    AccessCertificateIssuer,
    CertificateAlreadyIssuedError,
    ManualGrantDisabledError,
    MissingDeviceKeyError,
    PaymentNotSettledError,
)
from app.services.access.crypto.hashing import access_pass_commitment, access_pass_lookup_hash, sha256_prefixed
from app.services.access.payments.base import PAYMENT_STATUS_INVOICE_CREATED, PAYMENT_STATUS_PAID


def _key_pair() -> tuple[str, str]:
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
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    AccessPaymentIntent.__table__.create(bind=engine)
    AccessCertificate.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def key_pair() -> tuple[str, str]:
    return _key_pair()


@pytest.fixture()
def issuer(db_session: Session, key_pair: tuple[str, str]) -> AccessCertificateIssuer:
    private_key, public_key = key_pair
    return AccessCertificateIssuer(
        db_session,
        server_pepper="server-pepper-for-tests",
        issuer_private_key=private_key,
        issuer_public_key=public_key,
        issuer_key_id="issuer-key-1",
        certificate_ttl_days=30,
    )


def _payment_intent(db: Session, status: str = PAYMENT_STATUS_PAID, plan: PlanCode = PlanCode.PRO) -> AccessPaymentIntent:
    intent = AccessPaymentIntent(
        payment_method="btcpay",
        provider="btcpay",
        provider_invoice_id_hash="sha256:invoice",
        invoice_hash="sha256:invoice-payload",
        payment_id_hash="sha256:payment",
        amount_sats=50_000,
        plan_code=plan.value,
        status=status,
        metadata_json={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        paid_at=datetime.now(UTC) if status == PAYMENT_STATUS_PAID else None,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )
    db.add(intent)
    db.flush()
    return intent


def test_paid_payment_intent_issues_certificate(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key", device_class="cli_vault")

    stored = db_session.execute(select(AccessCertificate)).scalar_one()
    assert result.raw_access_pass.startswith("bbp_live_")
    assert result.certificate_fingerprint == stored.certificate_fingerprint
    assert stored.status == "active"
    assert stored.plan_code == PlanCode.PRO.value
    assert stored.device_key_fingerprint == sha256_prefixed("device-public-key")
    assert result.save_warning.startswith("Save this Bastion Access Pass now")


def test_unpaid_payment_intent_cannot_issue_certificate(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session, status=PAYMENT_STATUS_INVOICE_CREATED)

    with pytest.raises(PaymentNotSettledError):
        issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")


def test_raw_access_pass_is_returned_once_and_duplicate_is_rejected(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    first = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    with pytest.raises(CertificateAlreadyIssuedError):
        issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    assert first.raw_access_pass.startswith("bbp_live_")


def test_raw_access_pass_is_not_stored_in_db(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    stored = db_session.execute(select(AccessCertificate)).scalar_one()

    serialized = f"{stored.pass_lookup_hash} {stored.pass_commitment} {stored.public_keys_json} {stored.issuer_signature_json}"
    assert result.raw_access_pass not in serialized


def test_pass_lookup_hash_is_hmac_not_plain_sha256(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    stored = db_session.execute(select(AccessCertificate)).scalar_one()

    assert stored.pass_lookup_hash == access_pass_lookup_hash("server-pepper-for-tests", result.raw_access_pass)
    assert stored.pass_lookup_hash.startswith("hmac-sha256:")
    assert stored.pass_lookup_hash != sha256_prefixed(result.raw_access_pass)


def test_pass_commitment_is_sha256_commitment(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    stored = db_session.execute(select(AccessCertificate)).scalar_one()

    assert stored.pass_commitment == access_pass_commitment(result.raw_access_pass)
    assert stored.pass_commitment.startswith("sha256:")


def test_certificate_fingerprint_is_stable_for_canonical_payload(issuer: AccessCertificateIssuer) -> None:
    payload_a = {"b": 2, "a": 1, "issuer_signatures": {"classical": None}}
    payload_b = {"issuer_signatures": {"classical": None}, "a": 1, "b": 2}

    assert issuer.compute_certificate_fingerprint(payload_a) == issuer.compute_certificate_fingerprint(payload_b)


def test_tampered_certificate_payload_fails_verification(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)
    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    tampered = dict(result.access_certificate)
    tampered["plan_code"] = PlanCode.ENTERPRISE.value

    assert issuer.verify_certificate_payload(result.access_certificate) is True
    assert issuer.verify_certificate_payload(tampered) is False


def test_device_key_fingerprint_is_required(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    with pytest.raises(MissingDeviceKeyError):
        issuer.issue_certificate_for_paid_intent(intent.id)


def test_bitcoin_seed_private_key_fields_are_absent(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    serialized = str(result.access_certificate).lower()

    assert "bitcoin_seed" not in serialized
    assert "bitcoin_private_key" not in serialized
    assert "wallet_seed" not in serialized


def test_no_wildcard_scopes_are_issued(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session, plan=PlanCode.ENTERPRISE)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert not (set(result.access_certificate["scopes"]) & FORBIDDEN_SCOPES)
    assert "*" not in result.access_certificate["scopes"]


def test_lite_cannot_receive_pro_scopes(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session, plan=PlanCode.LITE)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert SIGNALS_ADVANCED_READ not in result.access_certificate["scopes"]


def test_pro_receives_pro_scopes(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session, plan=PlanCode.PRO)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert SIGNALS_ADVANCED_READ in result.access_certificate["scopes"]
    assert set(get_plan_scopes(PlanCode.PRO)) == set(result.access_certificate["scopes"])


def test_manual_grant_fails_when_disabled(issuer: AccessCertificateIssuer) -> None:
    with pytest.raises(ManualGrantDisabledError):
        issuer.issue_certificate_for_manual_grant(PlanCode.LITE, device_public_key="device-public-key")


def test_issuer_emits_audit_event_without_raw_secrets(db_session: Session, key_pair: tuple[str, str]) -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    private_key, public_key = key_pair
    issuer = AccessCertificateIssuer(
        db_session,
        server_pepper="server-pepper-for-tests",
        issuer_private_key=private_key,
        issuer_public_key=public_key,
        issuer_key_id="issuer-key-1",
        audit_emitter=lambda event_type, payload: events.append((event_type, payload)),
    )
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert events[0][0] == "certificate_issued"
    assert result.raw_access_pass not in str(events[0][1])
    assert "private_key" not in str(events[0][1]).lower()


def test_logs_do_not_contain_raw_access_pass(issuer: AccessCertificateIssuer, db_session: Session, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert result.raw_access_pass not in caplog.text


def test_pq_fields_are_null_when_not_implemented(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")

    assert result.access_certificate["issuer_signatures"]["post_quantum"] is None
    assert result.access_certificate["issuer_signatures"]["backup_hash_based"] is None
    assert result.access_certificate["public_keys"]["device_pq"] is None


def test_certificate_status_defaults_to_active(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    stored = db_session.execute(select(AccessCertificate)).scalar_one()

    assert stored.status == "active"


def test_certificate_expiry_is_set_correctly(issuer: AccessCertificateIssuer, db_session: Session) -> None:
    intent = _payment_intent(db_session)

    result = issuer.issue_certificate_for_paid_intent(intent.id, device_public_key="device-public-key")
    stored = db_session.execute(select(AccessCertificate)).scalar_one()

    assert result.expires_at.replace(tzinfo=None) == stored.expires_at
    assert 29 <= (stored.expires_at - stored.issued_at).days <= 30


def test_source_does_not_store_or_log_raw_access_pass() -> None:
    source = Path("app/services/access/certificate_issuer.py").read_text()

    assert "logger." not in source
    assert "raw_access_pass=" in source
