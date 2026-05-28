"""candle runs and provider snapshots

Revision ID: 20260527_0024
Revises: 20260526_0023
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "20260527_0024"
down_revision = "20260526_0023"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "candle_provider_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column("provider_name", sa.String(32), nullable=False),
        sa.Column("provider_price_open", sa.Float(), nullable=True),
        sa.Column("provider_price_high", sa.Float(), nullable=True),
        sa.Column("provider_price_low", sa.Float(), nullable=True),
        sa.Column("provider_price_close", sa.Float(), nullable=True),
        sa.Column("provider_volume", sa.Float(), nullable=True),
        sa.Column("provider_latency_ms", sa.Integer(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_health_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candle_provider_snapshots_candle_id", "candle_provider_snapshots", ["candle_id"])
    op.create_index("ix_candle_provider_snapshots_provider_name", "candle_provider_snapshots", ["provider_name"])

    op.create_table(
        "candle_build_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("source_point_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("build_status", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("build_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("degraded_reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("rebuild_reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candle_build_runs_timeframe", "candle_build_runs", ["timeframe"])

def downgrade() -> None:
    op.drop_index("ix_candle_build_runs_timeframe", table_name="candle_build_runs")
    op.drop_table("candle_build_runs")
    op.drop_index("ix_candle_provider_snapshots_provider_name", table_name="candle_provider_snapshots")
    op.drop_index("ix_candle_provider_snapshots_candle_id", table_name="candle_provider_snapshots")
    op.drop_table("candle_provider_snapshots")
