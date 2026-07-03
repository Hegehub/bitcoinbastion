"""production news price impact engine

Revision ID: 20260527_0032
Revises: 20260527_0031
"""

from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "20260527_0032"
down_revision = "20260527_0031"
branch_labels = None
depends_on = None

NEWS_PRICE_IMPACT_COLUMNS: list[sa.Column[Any]] = [
    sa.Column("price_at_publish", sa.Float(), nullable=True),
    sa.Column("price_after_15m", sa.Float(), nullable=True),
    sa.Column("price_after_1h", sa.Float(), nullable=True),
    sa.Column("price_after_4h", sa.Float(), nullable=True),
    sa.Column("price_after_24h", sa.Float(), nullable=True),
    sa.Column("change_15m_pct", sa.Float(), nullable=True),
    sa.Column("change_1h_pct", sa.Float(), nullable=True),
    sa.Column("change_4h_pct", sa.Float(), nullable=True),
    sa.Column("change_24h_pct", sa.Float(), nullable=True),
    sa.Column("absolute_change_15m", sa.Float(), nullable=True),
    sa.Column("absolute_change_1h", sa.Float(), nullable=True),
    sa.Column("absolute_change_4h", sa.Float(), nullable=True),
    sa.Column("absolute_change_24h", sa.Float(), nullable=True),
    sa.Column("sentiment_label", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    sa.Column("expected_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
    sa.Column("actual_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
    sa.Column("direction_match", sa.String(length=16), nullable=False, server_default="unknown"),
    sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("source_credibility_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
    sa.Column("impact_confidence_score", sa.Float(), nullable=False, server_default="0"),
    sa.Column("dominant_window", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
    sa.Column("volatility_context", sa.Float(), nullable=False, server_default="0"),
    sa.Column("liquidity_context", sa.String(length=32), nullable=False, server_default="unknown"),
    sa.Column("impact_band", sa.String(length=16), nullable=False, server_default="VERY_LOW"),
    sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
    sa.Column("limitations_json", sa.JSON(), nullable=False, server_default="{}"),
    sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    sa.Column("calculated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
]


def upgrade() -> None:
    with op.batch_alter_table("news_price_impacts") as batch_op:
        batch_op.alter_column("article_id", existing_type=sa.Integer(), nullable=True)
        for column in NEWS_PRICE_IMPACT_COLUMNS:
            batch_op.add_column(column)
        batch_op.create_index("ix_news_price_impacts_event_id", ["event_id"])
        batch_op.create_index(
            "ix_news_price_impacts_impact_confidence_score", ["impact_confidence_score"]
        )
        batch_op.create_index("ix_news_price_impacts_dominant_window", ["dominant_window"])
        batch_op.create_index("ix_news_price_impacts_impact_band", ["impact_band"])
        batch_op.create_index("uq_news_price_impacts_article_id", ["article_id"], unique=True)
        batch_op.create_index("uq_news_price_impacts_event_id", ["event_id"], unique=True)

    op.create_table(
        "impact_window_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "impact_id", sa.Integer(), sa.ForeignKey("news_price_impacts.id"), nullable=False
        ),
        sa.Column("window_name", sa.String(length=16), nullable=False),
        sa.Column("window_minutes", sa.Integer(), nullable=False),
        sa.Column("price_before", sa.Float(), nullable=True),
        sa.Column("price_after", sa.Float(), nullable=True),
        sa.Column("change_pct", sa.Float(), nullable=True),
        sa.Column("absolute_change", sa.Float(), nullable=True),
        sa.Column("volatility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "direction_match", sa.String(length=16), nullable=False, server_default="unknown"
        ),
        sa.Column("window_weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_impact_window_snapshots_impact_id", "impact_window_snapshots", ["impact_id"]
    )
    op.create_index(
        "ix_impact_window_snapshots_window_name", "impact_window_snapshots", ["window_name"]
    )

    op.create_table(
        "impact_confidence_breakdowns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "impact_id", sa.Integer(), sa.ForeignKey("news_price_impacts.id"), nullable=False
        ),
        sa.Column("btc_relevance_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_credibility_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_strength_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_match_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_confidence_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("volatility_component", sa.Float(), nullable=False, server_default="0"),
        sa.Column("final_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_impact_confidence_breakdowns_impact_id", "impact_confidence_breakdowns", ["impact_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_impact_confidence_breakdowns_impact_id", table_name="impact_confidence_breakdowns"
    )
    op.drop_table("impact_confidence_breakdowns")
    op.drop_index("ix_impact_window_snapshots_window_name", table_name="impact_window_snapshots")
    op.drop_index("ix_impact_window_snapshots_impact_id", table_name="impact_window_snapshots")
    op.drop_table("impact_window_snapshots")
    with op.batch_alter_table("news_price_impacts") as batch_op:
        for index in [
            "uq_news_price_impacts_event_id",
            "uq_news_price_impacts_article_id",
            "ix_news_price_impacts_impact_band",
            "ix_news_price_impacts_dominant_window",
            "ix_news_price_impacts_impact_confidence_score",
            "ix_news_price_impacts_event_id",
        ]:
            batch_op.drop_index(index)
        for column in reversed(NEWS_PRICE_IMPACT_COLUMNS):
            batch_op.drop_column(str(column.name))
        batch_op.alter_column("article_id", existing_type=sa.Integer(), nullable=False)
