"""metric usage events timeseries

Revision ID: 20260625_0060
Revises: 20260622_0059
Create Date: 2026-06-25
"""

from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260625_0060"
down_revision = "20260622_0059"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return index_name in {idx["name"] for idx in inspect(op.get_bind()).get_indexes(table_name)}


def _create_index_if_missing(table_name: str, index_name: str, columns: list[str]) -> None:
    if _table_exists(table_name) and not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _timescale_enabled() -> bool:
    return os.getenv("TIMESCALE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _timescale_create_extension_enabled() -> bool:
    return os.getenv("TIMESCALE_CREATE_EXTENSION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _prepare_timescale_hypertable() -> None:
    if not (_is_postgresql() and _timescale_enabled()):
        return
    if _timescale_create_extension_enabled():
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')
                   AND to_regclass('public.metric_usage_events') IS NOT NULL THEN
                    PERFORM create_hypertable('public.metric_usage_events', 'recorded_at', if_not_exists => TRUE);
                END IF;
            END
            $$;
            """))


def upgrade() -> None:
    if not _table_exists("metric_usage_events"):
        op.create_table(
            "metric_usage_events",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("decision", sa.String(length=32), nullable=False),
            sa.Column("metric_group", sa.String(length=80), nullable=True),
            sa.Column("metric_name", sa.String(length=120), nullable=True),
            sa.Column("feature_code", sa.String(length=120), nullable=True),
            sa.Column("endpoint", sa.String(length=200), nullable=True),
            sa.Column("method", sa.String(length=16), nullable=True),
            sa.Column("status_code", sa.Integer(), nullable=True),
            sa.Column("credit_cost", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("request_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("pass_lookup_hash", sa.String(length=128), nullable=True),
            sa.Column("workspace_id_hash", sa.String(length=128), nullable=True),
            sa.Column("api_key_hash", sa.String(length=128), nullable=True),
            sa.Column("session_id_hash", sa.String(length=128), nullable=True),
            sa.Column("device_binding_id", sa.String(length=128), nullable=True),
            sa.Column("telegram_binding_id", sa.String(length=128), nullable=True),
            sa.Column("sdk_client", sa.String(length=80), nullable=True),
            sa.Column("client_kind", sa.String(length=64), nullable=True),
            sa.Column("source_component", sa.String(length=120), nullable=False),
            sa.Column("risk_level", sa.String(length=32), nullable=True),
            sa.Column("policy_decision", sa.String(length=64), nullable=True),
            sa.Column("denial_reason", sa.String(length=160), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    _create_index_if_missing("metric_usage_events", "ix_metric_usage_recorded_at", ["recorded_at"])
    _create_index_if_missing(
        "metric_usage_events", "ix_metric_usage_group_recorded", ["metric_group", "recorded_at"]
    )
    _create_index_if_missing(
        "metric_usage_events", "ix_metric_usage_name_recorded", ["metric_name", "recorded_at"]
    )
    _create_index_if_missing(
        "metric_usage_events", "ix_metric_usage_pass_recorded", ["pass_lookup_hash", "recorded_at"]
    )
    _create_index_if_missing(
        "metric_usage_events",
        "ix_metric_usage_workspace_recorded",
        ["workspace_id_hash", "recorded_at"],
    )
    _create_index_if_missing(
        "metric_usage_events",
        "ix_metric_usage_api_key_recorded",
        ["api_key_hash", "recorded_at"],
    )
    _create_index_if_missing(
        "metric_usage_events",
        "ix_metric_usage_session_recorded",
        ["session_id_hash", "recorded_at"],
    )
    _create_index_if_missing(
        "metric_usage_events",
        "ix_metric_usage_source_recorded",
        ["source_component", "recorded_at"],
    )
    _create_index_if_missing(
        "metric_usage_events", "ix_metric_usage_decision_recorded", ["decision", "recorded_at"]
    )
    _prepare_timescale_hypertable()


def downgrade() -> None:
    if _table_exists("metric_usage_events"):
        op.drop_table("metric_usage_events")
