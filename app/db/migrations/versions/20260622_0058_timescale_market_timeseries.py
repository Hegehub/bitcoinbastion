"""timescale market time-series foundation

Revision ID: 20260622_0058
Revises: 20260620_0057
Create Date: 2026-06-22
"""

from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20260622_0058"
down_revision = "20260620_0057"
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


def _prepare_timescale_hypertables() -> None:
    if not (_is_postgresql() and _timescale_enabled()):
        return

    if _timescale_create_extension_enabled():
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                    IF to_regclass('public.btc_price_points') IS NOT NULL THEN
                        PERFORM create_hypertable('public.btc_price_points', 'observed_at', if_not_exists => TRUE);
                    END IF;
                    IF to_regclass('public.btc_candles') IS NOT NULL THEN
                        PERFORM create_hypertable('public.btc_candles', 'open_time', if_not_exists => TRUE);
                    END IF;
                    IF to_regclass('public.mempool_fee_snapshots') IS NOT NULL THEN
                        PERFORM create_hypertable('public.mempool_fee_snapshots', 'observed_at', if_not_exists => TRUE);
                    END IF;
                END IF;
            END
            $$;
            """))


def upgrade() -> None:
    if not _table_exists("mempool_fee_snapshots"):
        op.create_table(
            "mempool_fee_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source", sa.String(length=64), nullable=False, server_default="unknown"),
            sa.Column("observed_at", sa.DateTime(), nullable=False),
            sa.Column("fastest_fee_sat_vb", sa.Float(), nullable=True),
            sa.Column("half_hour_fee_sat_vb", sa.Float(), nullable=True),
            sa.Column("hour_fee_sat_vb", sa.Float(), nullable=True),
            sa.Column("economy_fee_sat_vb", sa.Float(), nullable=True),
            sa.Column("minimum_fee_sat_vb", sa.Float(), nullable=True),
            sa.Column("mempool_vsize", sa.Integer(), nullable=True),
            sa.Column("mempool_tx_count", sa.Integer(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    _create_index_if_missing(
        "btc_price_points",
        "ix_btc_price_points_pair_observed_at",
        ["pair", "observed_at"],
    )
    _create_index_if_missing(
        "btc_price_points",
        "ix_btc_price_points_provider_observed_at",
        ["provider", "observed_at"],
    )
    _create_index_if_missing(
        "btc_candles",
        "ix_btc_candles_timeframe_open_time",
        ["timeframe", "open_time"],
    )
    _create_index_if_missing(
        "btc_candles",
        "ix_btc_candles_timeframe_close_time",
        ["timeframe", "close_time"],
    )
    _create_index_if_missing(
        "mempool_fee_snapshots",
        "ix_mempool_fee_snapshots_source_observed_at",
        ["source", "observed_at"],
    )
    _create_index_if_missing(
        "mempool_fee_snapshots",
        "ix_mempool_fee_snapshots_observed_at",
        ["observed_at"],
    )

    _prepare_timescale_hypertables()


def downgrade() -> None:
    _drop_index_if_exists("mempool_fee_snapshots", "ix_mempool_fee_snapshots_observed_at")
    _drop_index_if_exists("mempool_fee_snapshots", "ix_mempool_fee_snapshots_source_observed_at")
    _drop_index_if_exists("btc_price_points", "ix_btc_price_points_provider_observed_at")
    _drop_index_if_exists("btc_price_points", "ix_btc_price_points_pair_observed_at")
    if _table_exists("mempool_fee_snapshots"):
        op.drop_table("mempool_fee_snapshots")
