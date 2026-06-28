"""provider source health timeseries

Revision ID: 20260622_0059
Revises: 20260622_0058
Create Date: 2026-06-22
"""

from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260622_0059"
down_revision = "20260622_0058"
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


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


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


def _json_type() -> sa.types.TypeEngine[object]:
    return sa.JSON()


def _create_snapshot_table(table_name: str, key_column: str) -> None:
    if _table_exists(table_name):
        return
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=key_column == "source_key"),
        sa.Column("source_key", sa.String(length=120), nullable=key_column == "provider_key"),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("domain", sa.String(length=64), nullable=False, server_default="generic"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_rate", sa.Float(), nullable=True),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("degraded_reason", sa.String(length=255), nullable=True),
        sa.Column("runtime_mode", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", _json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def _create_confidence_table(table_name: str, key_column: str) -> None:
    if _table_exists(table_name):
        return
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=key_column == "source_key"),
        sa.Column("source_key", sa.String(length=120), nullable=key_column == "provider_key"),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("domain", sa.String(length=64), nullable=False, server_default="generic"),
        sa.Column(
            "event_type", sa.String(length=64), nullable=False, server_default="confidence_changed"
        ),
        sa.Column("previous_confidence", sa.Float(), nullable=True),
        sa.Column("new_confidence", sa.Float(), nullable=True),
        sa.Column("confidence_delta", sa.Float(), nullable=True),
        sa.Column("reason_code", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="recorded"),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", _json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def _prepare_timescale_hypertables() -> None:
    if not (_is_postgresql() and _timescale_enabled()):
        return
    if _timescale_create_extension_enabled():
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                    IF to_regclass('public.provider_health_timeseries_snapshots') IS NOT NULL THEN
                        PERFORM create_hypertable('public.provider_health_timeseries_snapshots', 'observed_at', if_not_exists => TRUE);
                    END IF;
                    IF to_regclass('public.source_health_timeseries_snapshots') IS NOT NULL THEN
                        PERFORM create_hypertable('public.source_health_timeseries_snapshots', 'observed_at', if_not_exists => TRUE);
                    END IF;
                    IF to_regclass('public.provider_confidence_timeseries_events') IS NOT NULL THEN
                        PERFORM create_hypertable('public.provider_confidence_timeseries_events', 'observed_at', if_not_exists => TRUE);
                    END IF;
                    IF to_regclass('public.source_confidence_timeseries_events') IS NOT NULL THEN
                        PERFORM create_hypertable('public.source_confidence_timeseries_events', 'observed_at', if_not_exists => TRUE);
                    END IF;
                END IF;
            END
            $$;
            """))


def upgrade() -> None:
    _create_snapshot_table("provider_health_timeseries_snapshots", "provider_key")
    _create_snapshot_table("source_health_timeseries_snapshots", "source_key")
    _create_confidence_table("provider_confidence_timeseries_events", "provider_key")
    _create_confidence_table("source_confidence_timeseries_events", "source_key")

    _create_index_if_missing(
        "provider_health_timeseries_snapshots",
        "ix_provider_health_ts_provider_observed",
        ["provider_key", "observed_at"],
    )
    _create_index_if_missing(
        "provider_health_timeseries_snapshots",
        "ix_provider_health_ts_domain_observed",
        ["domain", "observed_at"],
    )
    _create_index_if_missing(
        "provider_health_timeseries_snapshots",
        "ix_provider_health_ts_status_observed",
        ["status", "observed_at"],
    )
    _create_index_if_missing(
        "provider_health_timeseries_snapshots",
        "ix_provider_health_ts_degraded_observed",
        ["is_degraded", "observed_at"],
    )
    _create_index_if_missing(
        "source_health_timeseries_snapshots",
        "ix_source_health_ts_source_observed",
        ["source_key", "observed_at"],
    )
    _create_index_if_missing(
        "source_health_timeseries_snapshots",
        "ix_source_health_ts_provider_observed",
        ["provider_key", "observed_at"],
    )
    _create_index_if_missing(
        "source_health_timeseries_snapshots",
        "ix_source_health_ts_domain_observed",
        ["domain", "observed_at"],
    )
    _create_index_if_missing(
        "source_health_timeseries_snapshots",
        "ix_source_health_ts_status_observed",
        ["status", "observed_at"],
    )
    _create_index_if_missing(
        "source_health_timeseries_snapshots",
        "ix_source_health_ts_degraded_observed",
        ["is_degraded", "observed_at"],
    )
    _create_index_if_missing(
        "provider_confidence_timeseries_events",
        "ix_provider_confidence_ts_provider_observed",
        ["provider_key", "observed_at"],
    )
    _create_index_if_missing(
        "provider_confidence_timeseries_events",
        "ix_provider_confidence_ts_domain_observed",
        ["domain", "observed_at"],
    )
    _create_index_if_missing(
        "source_confidence_timeseries_events",
        "ix_source_confidence_ts_source_observed",
        ["source_key", "observed_at"],
    )
    _create_index_if_missing(
        "source_confidence_timeseries_events",
        "ix_source_confidence_ts_domain_observed",
        ["domain", "observed_at"],
    )
    _prepare_timescale_hypertables()


def downgrade() -> None:
    for table_name in [
        "source_confidence_timeseries_events",
        "provider_confidence_timeseries_events",
        "source_health_timeseries_snapshots",
        "provider_health_timeseries_snapshots",
    ]:
        if _table_exists(table_name):
            op.drop_table(table_name)
