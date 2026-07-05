from datetime import UTC, datetime, timedelta

from sqlalchemy import UniqueConstraint

from app.db.base import Base
from app.db.models.access import (
    AccessAuditEvent,
    AccessCertificate,
    AccessChallenge,
    AccessDevice,
    AccessPaymentIntent,
    AccessRequestNonce,
    AccessRevocation,
    AccessSession,
    ChildApiKey,
    DelegatedPass,
    MetricUsage,
    RecoveryAttempt,
    RecoveryQuorum,
    SubscriptionEntitlement,
)

ACCESS_MODELS = (
    AccessPaymentIntent,
    AccessCertificate,
    SubscriptionEntitlement,
    AccessDevice,
    AccessChallenge,
    AccessSession,
    AccessRequestNonce,
    AccessRevocation,
    AccessAuditEvent,
    MetricUsage,
    ChildApiKey,
    DelegatedPass,
    RecoveryQuorum,
    RecoveryAttempt,
)

EXPECTED_TABLES = {
    "access_payment_intents",
    "access_certificates",
    "subscription_entitlements",
    "access_devices",
    "access_challenges",
    "access_sessions",
    "access_request_nonces",
    "access_revocations",
    "access_audit_events",
    "metric_usage",
    "child_api_keys",
    "delegated_passes",
    "recovery_quorums",
    "recovery_attempts",
}

FORBIDDEN_COLUMN_NAMES = {
    "password",
    "password_hash",
    "bearer_token",
    "jwt_token",
    "raw_pass",
    "raw_session",
    "bitcoin_seed",
    "seed_phrase",
    "private_key",
}


def _unique_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    unique_sets: set[tuple[str, ...]] = set()
    for column in table.columns:
        if column.unique:
            unique_sets.add((column.name,))
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique_sets.add(tuple(column.name for column in constraint.columns))
    for index in table.indexes:
        if index.unique:
            unique_sets.add(tuple(column.name for column in index.columns))
    return unique_sets


def test_access_models_import_cleanly() -> None:
    assert [model.__name__ for model in ACCESS_MODELS] == [
        "AccessPaymentIntent",
        "AccessCertificate",
        "SubscriptionEntitlement",
        "AccessDevice",
        "AccessChallenge",
        "AccessSession",
        "AccessRequestNonce",
        "AccessRevocation",
        "AccessAuditEvent",
        "MetricUsage",
        "ChildApiKey",
        "DelegatedPass",
        "RecoveryQuorum",
        "RecoveryAttempt",
    ]


def test_sqlalchemy_metadata_includes_all_access_tables() -> None:
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_access_models_do_not_define_forbidden_secret_columns() -> None:
    for model in ACCESS_MODELS:
        column_names = {column.name for column in model.__table__.columns}
        assert column_names.isdisjoint(FORBIDDEN_COLUMN_NAMES), model.__tablename__


def test_important_unique_constraints_are_present() -> None:
    assert ("certificate_fingerprint",) in _unique_column_sets("access_certificates")
    assert ("device_key_fingerprint",) in _unique_column_sets("access_devices")
    assert ("challenge_hash",) in _unique_column_sets("access_challenges")
    assert ("session_hash",) in _unique_column_sets("access_sessions")
    assert ("session_hash", "nonce_hash") in _unique_column_sets("access_request_nonces")
    assert ("event_hash",) in _unique_column_sets("access_audit_events")
    assert ("key_id_hash",) in _unique_column_sets("child_api_keys")
    assert ("delegated_pass_hash",) in _unique_column_sets("delegated_passes")
    assert ("attempt_hash",) in _unique_column_sets("recovery_attempts")


def test_revocation_target_index_exists() -> None:
    index_columns = {
        tuple(column.name for column in index.columns)
        for index in Base.metadata.tables["access_revocations"].indexes
    }

    assert ("target_type", "target_hash") in index_columns


def test_model_instances_can_be_constructed_with_minimal_valid_fields() -> None:
    now = datetime.now(UTC)
    later = now + timedelta(hours=1)

    instances = [
        AccessPaymentIntent(payment_method="btcpay", amount_sats=1000, plan_code="lite_pass", status="created"),
        AccessCertificate(
            pass_lookup_hash="plh_example",
            pass_commitment="commitment_example",
            certificate_fingerprint="cert_fp_example",
            plan_code="lite_pass",
            status="active",
            issuer_key_id="issuer_key_example",
            scopes_json=["trace:lite:read"],
            issuer_signature_json={"signature": "sig_example_not_real"},
            issued_at=now,
            expires_at=later,
        ),
        SubscriptionEntitlement(
            pass_lookup_hash="plh_example",
            plan_code="lite_pass",
            status="active",
            metric_entitlements_json={"groups": ["trace.lite"]},
            limits_json={"requests_per_minute": 30},
            issuer_signature_json={"signature": "sig_example_not_real"},
            valid_from=now,
            valid_until=later,
        ),
        AccessDevice(
            certificate_fingerprint="cert_fp_example",
            device_key_fingerprint="device_fp_example",
            device_public_key="device_public_example_not_real",
            device_class="desktop_vault",
            status="active",
        ),
        AccessChallenge(
            challenge_hash="challenge_hash_example",
            certificate_fingerprint="cert_fp_example",
            origin="https://example.invalid",
            requested_scopes_json=["trace:lite:read"],
            server_nonce_hash="server_nonce_hash_example",
            challenge_payload_hash="challenge_payload_hash_example",
            status="created",
            expires_at=later,
        ),
        AccessSession(
            session_hash="session_hash_example",
            certificate_fingerprint="cert_fp_example",
            device_key_fingerprint="device_fp_example",
            scopes_json=["trace:lite:read"],
            status="active",
            expires_at=later,
        ),
        AccessRequestNonce(session_hash="session_hash_example", nonce_hash="nonce_hash_example", timestamp=now),
        AccessRevocation(target_type="session", target_hash="session_hash_example", reason="operator_test", revocation_epoch=1),
        AccessAuditEvent(event_hash="event_hash_example", event_type="access.session.created", canonical_event_json={"redacted": True}),
        MetricUsage(pass_lookup_hash="plh_example", metric_group="trace.lite", metric_name="trace_score", credit_cost=1),
        ChildApiKey(
            parent_pass_lookup_hash="plh_example",
            key_id_hash="key_id_hash_example",
            key_secret_hash="key_secret_hash_example",
            scopes_json=["trace:lite:read"],
            status="active",
            expires_at=later,
        ),
        DelegatedPass(
            parent_pass_lookup_hash="plh_example",
            delegated_pass_hash="delegated_hash_example",
            scopes_json=["trace:lite:read"],
            constraints_json={"max_requests": 10},
            status="active",
            valid_from=now,
            valid_until=later,
        ),
        RecoveryQuorum(
            pass_lookup_hash="plh_example",
            quorum_type="pro_2_of_3",
            threshold_required=2,
            total_factors=3,
            factors_json=[{"factor": "desktop_vault"}],
            status="active",
        ),
        RecoveryAttempt(pass_lookup_hash="plh_example", attempt_hash="attempt_hash_example", status="started"),
    ]

    assert len(instances) == 14


def test_json_fields_accept_dicts_and_lists() -> None:
    certificate = AccessCertificate(
        pass_lookup_hash="plh_example",
        pass_commitment="commitment_example",
        certificate_fingerprint="cert_fp_example",
        plan_code="plus_pass",
        status="active",
        issuer_key_id="issuer_key_example",
        hash_suite_json={"hash": "sha256"},
        scopes_json=["trace:standard:read"],
        public_keys_json={"device": "device_public_example_not_real"},
        issuer_signature_json={"signature": "sig_example_not_real"},
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    session = AccessSession(
        session_hash="session_hash_example",
        certificate_fingerprint="cert_fp_example",
        device_key_fingerprint="device_fp_example",
        scopes_json=["trace:standard:read"],
        policy_context_json={"risk_level": "low"},
        status="active",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    assert certificate.hash_suite_json == {"hash": "sha256"}
    assert certificate.scopes_json == ["trace:standard:read"]
    assert session.policy_context_json == {"risk_level": "low"}
