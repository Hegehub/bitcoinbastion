"""production candle attribution engine

Revision ID: 20260527_0033
Revises: 20260527_0032
"""

from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "20260527_0033"
down_revision = "20260527_0032"
branch_labels = None
depends_on = None

CANDLE_ATTRIBUTION_COLUMNS: list[sa.Column[Any]] = [
    sa.Column("signal_id", sa.Integer(), nullable=True),
    sa.Column("candidate_rank", sa.Integer(), nullable=False, server_default="0"),
    sa.Column("event_before_candle_seconds", sa.Integer(), nullable=False, server_default="0"),
    sa.Column("event_inside_candle", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("event_after_candle_seconds", sa.Integer(), nullable=False, server_default="0"),
    sa.Column("candle_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
    sa.Column(
        "sentiment_direction_match", sa.String(length=16), nullable=False, server_default="unknown"
    ),
    sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("source_credibility_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("event_confidence", sa.Float(), nullable=False, server_default="0"),
    sa.Column("impact_confidence", sa.Float(), nullable=False, server_default="0"),
    sa.Column("historical_similarity_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("pattern_match_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("freshness_weight", sa.Float(), nullable=False, server_default="0"),
    sa.Column("volatility_weight", sa.Float(), nullable=False, server_default="0"),
    sa.Column("confidence_band", sa.String(length=16), nullable=False, server_default="LOW"),
    sa.Column("is_primary_candidate", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("is_operator_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("is_operator_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column(
        "operator_review_status", sa.String(length=32), nullable=False, server_default="pending"
    ),
    sa.Column("operator_note", sa.Text(), nullable=False, server_default=""),
    sa.Column("evidence_refs_json", sa.JSON(), nullable=False, server_default="{}"),
]


def upgrade() -> None:
    with op.batch_alter_table("candle_attributions") as batch_op:
        for column_def in CANDLE_ATTRIBUTION_COLUMNS:
            batch_op.add_column(column_def)
        batch_op.create_index("ix_candle_attributions_signal_id", ["signal_id"])
        batch_op.create_index("ix_candle_attributions_candidate_rank", ["candidate_rank"])
        batch_op.create_index("ix_candle_attributions_created_at", ["created_at"])

    op.create_table(
        "candle_attribution_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column(
            "candidate_type", sa.String(length=64), nullable=False, server_default="news_event"
        ),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("raw_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("normalized_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ranking_features_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("rejection_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for column_name in ["candle_id", "event_id", "article_id", "created_at"]:
        op.create_index(
            f"ix_candle_attribution_candidates_{column_name}",
            "candle_attribution_candidates",
            [column_name],
        )

    op.create_table(
        "attribution_context_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=False),
        sa.Column("market_volatility", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_regime", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("provider_health", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("active_news_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("macro_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("security_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("institutional_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("news_provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("timeline_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_attribution_context_snapshots_candle_id", "attribution_context_snapshots", ["candle_id"]
    )
    op.create_index(
        "ix_attribution_context_snapshots_created_at",
        "attribution_context_snapshots",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attribution_context_snapshots_created_at", table_name="attribution_context_snapshots"
    )
    op.drop_index(
        "ix_attribution_context_snapshots_candle_id", table_name="attribution_context_snapshots"
    )
    op.drop_table("attribution_context_snapshots")
    for column_name in ["created_at", "article_id", "event_id", "candle_id"]:
        op.drop_index(
            f"ix_candle_attribution_candidates_{column_name}",
            table_name="candle_attribution_candidates",
        )
    op.drop_table("candle_attribution_candidates")
    with op.batch_alter_table("candle_attributions") as batch_op:
        batch_op.drop_index("ix_candle_attributions_created_at")
        batch_op.drop_index("ix_candle_attributions_candidate_rank")
        batch_op.drop_index("ix_candle_attributions_signal_id")
        for column_def in reversed(CANDLE_ATTRIBUTION_COLUMNS):
            batch_op.drop_column(str(column_def.name))
