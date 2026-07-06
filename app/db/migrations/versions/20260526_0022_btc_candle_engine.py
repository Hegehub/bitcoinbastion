"""btc candle engine

Revision ID: 20260526_0022
Revises: 20260526_0021
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0022"
down_revision = "20260526_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "btc_candles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("open_time", sa.DateTime(), nullable=False),
        sa.Column("close_time", sa.DateTime(), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=False),
        sa.Column("high_price", sa.Float(), nullable=False),
        sa.Column("low_price", sa.Float(), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("volume_estimate", sa.Float(), nullable=True),
        sa.Column("trade_count_estimate", sa.Integer(), nullable=True),
        sa.Column(
            "source_mode", sa.String(32), nullable=False, server_default="multi_provider_median"
        ),
        sa.Column("provider_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_point_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("median_price_source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("integrity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_rebuilt", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rebuilt_at", sa.DateTime(), nullable=True),
        sa.Column("calculation_version", sa.String(32), nullable=False, server_default="v1"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("timeframe", "open_time", name="uq_btc_candles_timeframe_open_time"),
    )
    op.create_index("ix_btc_candles_timeframe_open_time", "btc_candles", ["timeframe", "open_time"])
    op.create_index(
        "ix_btc_candles_timeframe_close_time", "btc_candles", ["timeframe", "close_time"]
    )


def downgrade() -> None:
    op.drop_index("ix_btc_candles_timeframe_close_time", table_name="btc_candles")
    op.drop_index("ix_btc_candles_timeframe_open_time", table_name="btc_candles")
    op.drop_table("btc_candles")
