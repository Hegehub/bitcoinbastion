"""align models schema truth

Revision ID: 9ecab5c090cf
Revises: 20260416_0007
Create Date: 2026-04-18 16:19:28.827116
"""

from alembic import op
from sqlalchemy import inspect

revision = "9ecab5c090cf"
down_revision = "20260416_0007"
branch_labels = None
depends_on = None


def _create_index_if_missing(name: str, table: str, columns: list[str], *, unique: bool = False) -> None:
    bind = op.get_bind()
    existing = {idx["name"] for idx in inspect(bind).get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns, unique=unique)


def _drop_index_if_exists(name: str, table: str) -> None:
    bind = op.get_bind()
    existing = {idx["name"] for idx in inspect(bind).get_indexes(table)}
    if name in existing:
        op.drop_index(name, table_name=table)


def upgrade() -> None:
    _create_index_if_missing("ix_audit_logs_action", "audit_logs", ["action"])
    _create_index_if_missing("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    _create_index_if_missing("ix_delivery_logs_signal_id", "delivery_logs", ["signal_id"])
    _create_index_if_missing("ix_delivery_logs_user_id", "delivery_logs", ["user_id"])
    _create_index_if_missing("ix_entities_name", "entities", ["name"])
    _create_index_if_missing("ix_entity_addresses_address", "entity_addresses", ["address"])
    _create_index_if_missing("ix_entity_addresses_entity_id", "entity_addresses", ["entity_id"])
    _create_index_if_missing("ix_psbt_workflows_treasury_request_id", "psbt_workflows", ["treasury_request_id"])
    _create_index_if_missing("ix_signal_source_links_signal_id", "signal_source_links", ["signal_id"])
    _create_index_if_missing("ix_user_subscriptions_plan_id", "user_subscriptions", ["plan_id"])
    _create_index_if_missing("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"])
    _create_index_if_missing(
        "ix_wallet_health_reports_wallet_profile_id", "wallet_health_reports", ["wallet_profile_id"]
    )
    _create_index_if_missing("ix_wallet_profiles_user_id", "wallet_profiles", ["user_id"])


def downgrade() -> None:
    _drop_index_if_exists("ix_wallet_profiles_user_id", "wallet_profiles")
    _drop_index_if_exists("ix_wallet_health_reports_wallet_profile_id", "wallet_health_reports")
    _drop_index_if_exists("ix_user_subscriptions_user_id", "user_subscriptions")
    _drop_index_if_exists("ix_user_subscriptions_plan_id", "user_subscriptions")
    _drop_index_if_exists("ix_signal_source_links_signal_id", "signal_source_links")
    _drop_index_if_exists("ix_psbt_workflows_treasury_request_id", "psbt_workflows")
    _drop_index_if_exists("ix_entity_addresses_entity_id", "entity_addresses")
    _drop_index_if_exists("ix_entity_addresses_address", "entity_addresses")
    _drop_index_if_exists("ix_entities_name", "entities")
    _drop_index_if_exists("ix_delivery_logs_user_id", "delivery_logs")
    _drop_index_if_exists("ix_delivery_logs_signal_id", "delivery_logs")
    _drop_index_if_exists("ix_audit_logs_actor_user_id", "audit_logs")
    _drop_index_if_exists("ix_audit_logs_action", "audit_logs")
