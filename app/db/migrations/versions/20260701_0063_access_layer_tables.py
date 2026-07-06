"""access layer tables

Revision ID: 20260701_0063
Revises: 20260629_0062
Create Date: 2026-07-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260701_0063"
down_revision = "20260629_0062"
branch_labels = None
depends_on = None

PLAN_CODES = ("lite_pass", "basic_pass", "plus_pass", "pro_pass", "business_pass", "enterprise_pass")
PAYMENT_STATUSES = ("created", "pending", "settled", "expired", "invalid", "cancelled", "failed")
CERTIFICATE_STATUSES = ("active", "expired", "revoked", "frozen", "replaced")
ENTITLEMENT_STATUSES = ("active", "grace", "expired", "revoked", "frozen", "upgraded", "downgraded")
DEVICE_STATUSES = ("active", "pending", "revoked", "frozen", "replaced")
CHALLENGE_STATUSES = ("created", "used", "expired", "revoked")
SESSION_STATUSES = ("active", "expired", "revoked", "frozen")
REVOCATION_TARGET_TYPES = (
    "pass",
    "certificate",
    "entitlement",
    "device",
    "session",
    "child_api_key",
    "delegated_pass",
    "offline_pack",
    "issuer_key",
)
RECOVERY_ATTEMPT_STATUSES = (
    "started",
    "factor_verified",
    "cooldown",
    "completed",
    "failed",
    "cancelled",
    "locked",
)


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _json_type() -> sa.types.TypeEngine[object]:
    return sa.JSON()


def _enum_check(column_name: str, values: tuple[str, ...], constraint_name: str) -> sa.CheckConstraint:
    quoted = ", ".join(f"'{value}'" for value in values)
    return sa.CheckConstraint(f"{column_name} IN ({quoted})", name=constraint_name)


def _drop_table_if_exists(table_name: str) -> None:
    if _table_exists(table_name):
        op.drop_table(table_name)


def upgrade() -> None:
    if not _table_exists("access_payment_intents"):
        op.create_table(
            "access_payment_intents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("payment_method", sa.String(length=40), nullable=False),
            sa.Column("provider", sa.String(length=80), nullable=True),
            sa.Column("provider_invoice_id_hash", sa.String(length=128), nullable=True),
            sa.Column("invoice_hash", sa.String(length=128), nullable=True),
            sa.Column("payment_id_hash", sa.String(length=128), nullable=True),
            sa.Column("amount_sats", sa.Integer(), nullable=False),
            sa.Column("plan_code", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("paid_at", sa.DateTime(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("amount_sats >= 0", name="ck_access_payment_intents_amount_sats_nonnegative"),
            _enum_check("status", PAYMENT_STATUSES, "ck_access_payment_intents_status"),
            _enum_check("plan_code", PLAN_CODES, "ck_access_payment_intents_plan_code"),
        )
        op.create_index("ix_access_payment_intents_payment_id_hash", "access_payment_intents", ["payment_id_hash"])
        op.create_index("ix_access_payment_intents_invoice_hash", "access_payment_intents", ["invoice_hash"])
        op.create_index("ix_access_payment_intents_status", "access_payment_intents", ["status"])
        op.create_index("ix_access_payment_intents_plan_code", "access_payment_intents", ["plan_code"])

    if not _table_exists("access_certificates"):
        op.create_table(
            "access_certificates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("pass_commitment", sa.String(length=128), nullable=False),
            sa.Column("certificate_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("payment_intent_id", sa.Integer(), sa.ForeignKey("access_payment_intents.id"), nullable=True),
            sa.Column("plan_code", sa.String(length=40), nullable=False),
            sa.Column("scopes_json", _json_type(), nullable=False),
            sa.Column("device_key_fingerprint", sa.String(length=128), nullable=True),
            sa.Column("issuer_key_id", sa.String(length=120), nullable=False),
            sa.Column("issuer_signature_json", _json_type(), nullable=False),
            sa.Column("crypto_epoch", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("hash_suite_json", _json_type(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("issued_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("certificate_fingerprint", name="uq_access_certificates_certificate_fingerprint"),
            sa.UniqueConstraint("pass_lookup_hash", name="uq_access_certificates_pass_lookup_hash"),
            _enum_check("plan_code", PLAN_CODES, "ck_access_certificates_plan_code"),
            _enum_check("status", CERTIFICATE_STATUSES, "ck_access_certificates_status"),
        )
        op.create_index("ix_access_certificates_pass_lookup_hash", "access_certificates", ["pass_lookup_hash"])
        op.create_index(
            "ix_access_certificates_certificate_fingerprint",
            "access_certificates",
            ["certificate_fingerprint"],
        )
        op.create_index(
            "ix_access_certificates_device_key_fingerprint",
            "access_certificates",
            ["device_key_fingerprint"],
        )
        op.create_index("ix_access_certificates_status", "access_certificates", ["status"])
        op.create_index("ix_access_certificates_plan_code", "access_certificates", ["plan_code"])

    if not _table_exists("subscription_entitlements"):
        op.create_table(
            "subscription_entitlements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("plan_code", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("metric_entitlements_json", _json_type(), nullable=False),
            sa.Column("limits_json", _json_type(), nullable=False),
            sa.Column("valid_from", sa.DateTime(), nullable=False),
            sa.Column("valid_until", sa.DateTime(), nullable=False),
            sa.Column("grace_until", sa.DateTime(), nullable=True),
            sa.Column("issuer_signature_json", _json_type(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("valid_until > valid_from", name="ck_subscription_entitlements_valid_window"),
            _enum_check("plan_code", PLAN_CODES, "ck_subscription_entitlements_plan_code"),
            _enum_check("status", ENTITLEMENT_STATUSES, "ck_subscription_entitlements_status"),
        )
        op.create_index("ix_subscription_entitlements_pass_lookup_hash", "subscription_entitlements", ["pass_lookup_hash"])
        op.create_index(
            "ix_subscription_entitlements_access_certificate_id",
            "subscription_entitlements",
            ["access_certificate_id"],
        )
        op.create_index("ix_subscription_entitlements_plan_code", "subscription_entitlements", ["plan_code"])
        op.create_index("ix_subscription_entitlements_status", "subscription_entitlements", ["status"])
        op.create_index("ix_subscription_entitlements_valid_until", "subscription_entitlements", ["valid_until"])

    if not _table_exists("access_devices"):
        op.create_table(
            "access_devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("device_key_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("device_public_key", sa.Text(), nullable=False),
            sa.Column("device_class", sa.String(length=40), nullable=False),
            sa.Column("attestation_type", sa.String(length=80), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("first_seen_at", sa.DateTime(), nullable=True),
            sa.Column("last_seen_at", sa.DateTime(), nullable=True),
            sa.Column("risk_score", sa.Integer(), nullable=False),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint(
                "access_certificate_id",
                "device_key_fingerprint",
                name="uq_access_devices_certificate_device_fingerprint",
            ),
            sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_access_devices_risk_score_range"),
            _enum_check("status", DEVICE_STATUSES, "ck_access_devices_status"),
        )
        op.create_index("ix_access_devices_access_certificate_id", "access_devices", ["access_certificate_id"])
        op.create_index("ix_access_devices_device_key_fingerprint", "access_devices", ["device_key_fingerprint"])
        op.create_index("ix_access_devices_status", "access_devices", ["status"])

    if not _table_exists("access_challenges"):
        op.create_table(
            "access_challenges",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("certificate_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("origin", sa.String(length=2048), nullable=False),
            sa.Column("requested_scopes_json", _json_type(), nullable=False),
            sa.Column("challenge_hash", sa.String(length=128), nullable=False),
            sa.Column("server_nonce_hash", sa.String(length=128), nullable=False),
            sa.Column("client_nonce_hash", sa.String(length=128), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("challenge_hash", name="uq_access_challenges_challenge_hash"),
            _enum_check("status", CHALLENGE_STATUSES, "ck_access_challenges_status"),
        )
        op.create_index("ix_access_challenges_certificate_fingerprint", "access_challenges", ["certificate_fingerprint"])
        op.create_index("ix_access_challenges_challenge_hash", "access_challenges", ["challenge_hash"])
        op.create_index("ix_access_challenges_status", "access_challenges", ["status"])
        op.create_index("ix_access_challenges_expires_at", "access_challenges", ["expires_at"])

    if not _table_exists("access_sessions"):
        op.create_table(
            "access_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_hash", sa.String(length=128), nullable=False),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("access_device_id", sa.Integer(), sa.ForeignKey("access_devices.id"), nullable=False),
            sa.Column("session_key_fingerprint", sa.String(length=128), nullable=True),
            sa.Column("scopes_json", _json_type(), nullable=False),
            sa.Column("plan_code", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("risk_level", sa.String(length=30), nullable=False),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.UniqueConstraint("session_hash", name="uq_access_sessions_session_hash"),
            _enum_check("plan_code", PLAN_CODES, "ck_access_sessions_plan_code"),
            _enum_check("status", SESSION_STATUSES, "ck_access_sessions_status"),
        )
        op.create_index("ix_access_sessions_session_hash", "access_sessions", ["session_hash"])
        op.create_index("ix_access_sessions_access_certificate_id", "access_sessions", ["access_certificate_id"])
        op.create_index("ix_access_sessions_access_device_id", "access_sessions", ["access_device_id"])
        op.create_index("ix_access_sessions_status", "access_sessions", ["status"])
        op.create_index("ix_access_sessions_expires_at", "access_sessions", ["expires_at"])

    if not _table_exists("access_request_nonces"):
        op.create_table(
            "access_request_nonces",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("access_session_id", sa.Integer(), sa.ForeignKey("access_sessions.id"), nullable=False),
            sa.Column("nonce_hash", sa.String(length=128), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("access_session_id", "nonce_hash", name="uq_access_request_nonces_session_nonce"),
        )
        op.create_index("ix_access_request_nonces_access_session_id", "access_request_nonces", ["access_session_id"])
        op.create_index("ix_access_request_nonces_nonce_hash", "access_request_nonces", ["nonce_hash"])
        op.create_index("ix_access_request_nonces_created_at", "access_request_nonces", ["created_at"])

    if not _table_exists("access_revocations"):
        op.create_table(
            "access_revocations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("target_type", sa.String(length=40), nullable=False),
            sa.Column("target_hash", sa.String(length=128), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=False),
            sa.Column("revocation_epoch", sa.Integer(), nullable=False),
            sa.Column("signature_id", sa.String(length=120), nullable=True),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("target_type", "target_hash", name="uq_access_revocations_target"),
            _enum_check("target_type", REVOCATION_TARGET_TYPES, "ck_access_revocations_target_type"),
        )
        op.create_index("ix_access_revocations_target_type", "access_revocations", ["target_type"])
        op.create_index("ix_access_revocations_target_hash", "access_revocations", ["target_hash"])
        op.create_index("ix_access_revocations_revocation_epoch", "access_revocations", ["revocation_epoch"])
        op.create_index("ix_access_revocations_created_at", "access_revocations", ["created_at"])

    if not _table_exists("access_audit_events"):
        op.create_table(
            "access_audit_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("event_hash", sa.String(length=128), nullable=False),
            sa.Column("previous_event_hash", sa.String(length=128), nullable=True),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("actor_hash", sa.String(length=128), nullable=True),
            sa.Column("object_hash", sa.String(length=128), nullable=True),
            sa.Column("canonical_event_json", _json_type(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("event_hash", name="uq_access_audit_events_event_hash"),
        )
        op.create_index("ix_access_audit_events_event_hash", "access_audit_events", ["event_hash"])
        op.create_index("ix_access_audit_events_previous_event_hash", "access_audit_events", ["previous_event_hash"])
        op.create_index("ix_access_audit_events_event_type", "access_audit_events", ["event_type"])
        op.create_index("ix_access_audit_events_actor_hash", "access_audit_events", ["actor_hash"])
        op.create_index("ix_access_audit_events_object_hash", "access_audit_events", ["object_hash"])
        op.create_index("ix_access_audit_events_created_at", "access_audit_events", ["created_at"])

    if not _table_exists("metric_usage"):
        op.create_table(
            "metric_usage",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("access_session_id", sa.Integer(), sa.ForeignKey("access_sessions.id"), nullable=True),
            sa.Column("metric_group", sa.String(length=120), nullable=False),
            sa.Column("metric_name", sa.String(length=160), nullable=False),
            sa.Column("credit_cost", sa.Integer(), nullable=False),
            sa.Column("request_hash", sa.String(length=128), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.CheckConstraint("credit_cost >= 0", name="ck_metric_usage_credit_cost_nonnegative"),
        )
        op.create_index("ix_metric_usage_pass_lookup_hash", "metric_usage", ["pass_lookup_hash"])
        op.create_index("ix_metric_usage_access_session_id", "metric_usage", ["access_session_id"])
        op.create_index("ix_metric_usage_metric_group", "metric_usage", ["metric_group"])
        op.create_index("ix_metric_usage_metric_name", "metric_usage", ["metric_name"])
        op.create_index("ix_metric_usage_timestamp", "metric_usage", ["timestamp"])
        op.create_index("ix_metric_usage_request_hash", "metric_usage", ["request_hash"])

    if not _table_exists("child_api_keys"):
        op.create_table(
            "child_api_keys",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("parent_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("parent_pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("key_id_hash", sa.String(length=128), nullable=False),
            sa.Column("key_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=True),
            sa.Column("scopes_json", _json_type(), nullable=False),
            sa.Column("limits_json", _json_type(), nullable=True),
            sa.Column("cannot_access_json", _json_type(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.UniqueConstraint("key_id_hash", name="uq_child_api_keys_key_id_hash"),
            _enum_check("status", SESSION_STATUSES, "ck_child_api_keys_status"),
        )
        op.create_index("ix_child_api_keys_parent_certificate_id", "child_api_keys", ["parent_certificate_id"])
        op.create_index("ix_child_api_keys_parent_pass_lookup_hash", "child_api_keys", ["parent_pass_lookup_hash"])
        op.create_index("ix_child_api_keys_key_id_hash", "child_api_keys", ["key_id_hash"])
        op.create_index("ix_child_api_keys_status", "child_api_keys", ["status"])
        op.create_index("ix_child_api_keys_expires_at", "child_api_keys", ["expires_at"])

    if not _table_exists("delegated_passes"):
        op.create_table(
            "delegated_passes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("parent_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("parent_pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("delegated_pass_hash", sa.String(length=128), nullable=False),
            sa.Column("delegated_to_hash", sa.String(length=128), nullable=True),
            sa.Column("scopes_json", _json_type(), nullable=False),
            sa.Column("limits_json", _json_type(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.UniqueConstraint("delegated_pass_hash", name="uq_delegated_passes_delegated_pass_hash"),
            _enum_check("status", SESSION_STATUSES, "ck_delegated_passes_status"),
        )
        op.create_index("ix_delegated_passes_parent_certificate_id", "delegated_passes", ["parent_certificate_id"])
        op.create_index("ix_delegated_passes_parent_pass_lookup_hash", "delegated_passes", ["parent_pass_lookup_hash"])
        op.create_index("ix_delegated_passes_delegated_pass_hash", "delegated_passes", ["delegated_pass_hash"])
        op.create_index("ix_delegated_passes_status", "delegated_passes", ["status"])
        op.create_index("ix_delegated_passes_expires_at", "delegated_passes", ["expires_at"])

    if not _table_exists("recovery_quorums"):
        op.create_table(
            "recovery_quorums",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("pass_lookup_hash", sa.String(length=128), nullable=False),
            sa.Column("quorum_type", sa.String(length=80), nullable=False),
            sa.Column("required_shares", sa.Integer(), nullable=False),
            sa.Column("total_shares", sa.Integer(), nullable=False),
            sa.Column("policy_json", _json_type(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("required_shares >= 1", name="ck_recovery_quorums_required_shares_min"),
            sa.CheckConstraint("required_shares <= total_shares", name="ck_recovery_quorums_required_lte_total"),
            _enum_check("status", CERTIFICATE_STATUSES, "ck_recovery_quorums_status"),
        )
        op.create_index("ix_recovery_quorums_access_certificate_id", "recovery_quorums", ["access_certificate_id"])
        op.create_index("ix_recovery_quorums_pass_lookup_hash", "recovery_quorums", ["pass_lookup_hash"])
        op.create_index("ix_recovery_quorums_status", "recovery_quorums", ["status"])

    if not _table_exists("recovery_attempts"):
        op.create_table(
            "recovery_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recovery_quorum_id", sa.Integer(), sa.ForeignKey("recovery_quorums.id"), nullable=False),
            sa.Column("access_certificate_id", sa.Integer(), sa.ForeignKey("access_certificates.id"), nullable=False),
            sa.Column("attempt_hash", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("verified_factors_json", _json_type(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("cooldown_until", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("failed_reason", sa.String(length=255), nullable=True),
            sa.Column("metadata_json", _json_type(), nullable=True),
            sa.UniqueConstraint("attempt_hash", name="uq_recovery_attempts_attempt_hash"),
            _enum_check("status", RECOVERY_ATTEMPT_STATUSES, "ck_recovery_attempts_status"),
        )
        op.create_index("ix_recovery_attempts_recovery_quorum_id", "recovery_attempts", ["recovery_quorum_id"])
        op.create_index("ix_recovery_attempts_access_certificate_id", "recovery_attempts", ["access_certificate_id"])
        op.create_index("ix_recovery_attempts_attempt_hash", "recovery_attempts", ["attempt_hash"])
        op.create_index("ix_recovery_attempts_status", "recovery_attempts", ["status"])
        op.create_index("ix_recovery_attempts_started_at", "recovery_attempts", ["started_at"])
        op.create_index("ix_recovery_attempts_cooldown_until", "recovery_attempts", ["cooldown_until"])


def downgrade() -> None:
    for table_name in (
        "recovery_attempts",
        "recovery_quorums",
        "delegated_passes",
        "child_api_keys",
        "metric_usage",
        "access_audit_events",
        "access_revocations",
        "access_request_nonces",
        "access_sessions",
        "access_challenges",
        "access_devices",
        "subscription_entitlements",
        "access_certificates",
        "access_payment_intents",
    ):
        _drop_table_if_exists(table_name)
