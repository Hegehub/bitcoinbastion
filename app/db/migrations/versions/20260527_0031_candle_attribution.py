"""candle attribution engine foundation

Revision ID: 20260527_0031
Revises: 20260527_0030
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0031"
down_revision = "20260527_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candle_attributions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("timeframe", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("candle_open_time", sa.DateTime(), nullable=False),
        sa.Column("candle_close_time", sa.DateTime(), nullable=False),
        sa.Column("attribution_type", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("candidate_category", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("time_distance_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_distance_weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_move_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("direction_match", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("event_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_used", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("dominant_window", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("summary_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for column in ["candle_id", "event_id", "article_id", "timeframe", "confidence_score", "rank"]:
        op.create_index(f"ix_candle_attributions_{column}", "candle_attributions", [column])

    op.create_table(
        "attribution_replay_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False, server_default="candle-attribution-v1"),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("candidate_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeline_window_before_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeline_window_after_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ranking_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("explanation_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_attribution_replay_logs_candle_id", "attribution_replay_logs", ["candle_id"])
    op.create_index("ix_attribution_replay_logs_input_hash", "attribution_replay_logs", ["input_hash"])


def downgrade() -> None:
    op.drop_index("ix_attribution_replay_logs_input_hash", table_name="attribution_replay_logs")
    op.drop_index("ix_attribution_replay_logs_candle_id", table_name="attribution_replay_logs")
    op.drop_table("attribution_replay_logs")
    for column in ["rank", "confidence_score", "timeframe", "article_id", "event_id", "candle_id"]:
        op.drop_index(f"ix_candle_attributions_{column}", table_name="candle_attributions")
    op.drop_table("candle_attributions")
