"""candle attribution foundation context

Revision ID: 20260527_0034
Revises: 20260527_0033
"""

from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "20260527_0034"
down_revision = "20260527_0033"
branch_labels = None
depends_on = None

CANDIDATE_COLUMNS: list[sa.Column[Any]] = [
    sa.Column("time_distance_seconds", sa.Integer(), nullable=False, server_default="0"),
    sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("direction_match_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("impact_alignment_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("recency_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
]


def upgrade() -> None:
    with op.batch_alter_table("candle_attribution_candidates") as batch_op:
        for column_def in CANDIDATE_COLUMNS:
            batch_op.add_column(column_def)

    op.create_table(
        "candle_context_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column("volatility_level", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("volume_level", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_regime", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("news_density", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_density", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positive_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("macro_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("security_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("regulatory_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("institutional_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candle_context_snapshots_candle_id", "candle_context_snapshots", ["candle_id"])
    op.create_index("ix_candle_context_snapshots_created_at", "candle_context_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_candle_context_snapshots_created_at", table_name="candle_context_snapshots")
    op.drop_index("ix_candle_context_snapshots_candle_id", table_name="candle_context_snapshots")
    op.drop_table("candle_context_snapshots")
    with op.batch_alter_table("candle_attribution_candidates") as batch_op:
        for column_def in reversed(CANDIDATE_COLUMNS):
            batch_op.drop_column(str(column_def.name))
