"""production market memory engine

Revision ID: 20260527_0044
Revises: 20260527_0043
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0044"
down_revision = "20260527_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_memory_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column(
            "memory_type", sa.String(length=64), nullable=False, server_default="historical_context"
        ),
        sa.Column("memory_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_market_memory_records_event_id", "market_memory_records", ["event_id"])
    op.create_index("ix_market_memory_records_pattern_id", "market_memory_records", ["pattern_id"])
    op.create_index(
        "ix_market_memory_records_memory_type", "market_memory_records", ["memory_type"]
    )
    op.create_index(
        "ix_market_memory_records_memory_score", "market_memory_records", ["memory_score"]
    )
    op.create_index(
        "ix_market_memory_records_confidence_score", "market_memory_records", ["confidence_score"]
    )

    op.create_table(
        "event_fingerprints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("institutional_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("macro_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("regulatory_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("security_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_change_15m", sa.Float(), nullable=True),
        sa.Column("price_change_1h", sa.Float(), nullable=True),
        sa.Column("price_change_4h", sa.Float(), nullable=True),
        sa.Column("price_change_24h", sa.Float(), nullable=True),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
        sa.Column("volatility_profile", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_event_fingerprints_event_id", "event_fingerprints", ["event_id"], unique=True
    )
    op.create_index("ix_event_fingerprints_direction", "event_fingerprints", ["direction"])
    op.create_index(
        "ix_event_fingerprints_confidence_score", "event_fingerprints", ["confidence_score"]
    )

    op.create_table(
        "pattern_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column("pattern_slug", sa.String(length=96), nullable=False, server_default=""),
        sa.Column("historical_occurrences", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("median_15m_move", sa.Float(), nullable=True),
        sa.Column("median_1h_move", sa.Float(), nullable=True),
        sa.Column("median_4h_move", sa.Float(), nullable=True),
        sa.Column("median_24h_move", sa.Float(), nullable=True),
        sa.Column("positive_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("negative_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("neutral_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("best_case_move", sa.Float(), nullable=True),
        sa.Column("worst_case_move", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_pattern_statistics_pattern_id", "pattern_statistics", ["pattern_id"], unique=True
    )
    op.create_index("ix_pattern_statistics_pattern_slug", "pattern_statistics", ["pattern_slug"])

    op.create_table(
        "market_memory_operator_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=True),
        sa.Column("similar_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("override_confidence", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("false_similarity", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("audit_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_market_memory_operator_reviews_event_id", "market_memory_operator_reviews", ["event_id"]
    )
    op.create_index(
        "ix_market_memory_operator_reviews_pattern_id",
        "market_memory_operator_reviews",
        ["pattern_id"],
    )
    op.create_index(
        "ix_market_memory_operator_reviews_similar_event_id",
        "market_memory_operator_reviews",
        ["similar_event_id"],
    )
    op.create_index(
        "ix_market_memory_operator_reviews_action", "market_memory_operator_reviews", ["action"]
    )
    op.create_index(
        "ix_market_memory_operator_reviews_false_similarity",
        "market_memory_operator_reviews",
        ["false_similarity"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_market_memory_operator_reviews_false_similarity",
        table_name="market_memory_operator_reviews",
    )
    op.drop_index(
        "ix_market_memory_operator_reviews_action", table_name="market_memory_operator_reviews"
    )
    op.drop_index(
        "ix_market_memory_operator_reviews_similar_event_id",
        table_name="market_memory_operator_reviews",
    )
    op.drop_index(
        "ix_market_memory_operator_reviews_pattern_id", table_name="market_memory_operator_reviews"
    )
    op.drop_index(
        "ix_market_memory_operator_reviews_event_id", table_name="market_memory_operator_reviews"
    )
    op.drop_table("market_memory_operator_reviews")
    op.drop_index("ix_pattern_statistics_pattern_slug", table_name="pattern_statistics")
    op.drop_index("ix_pattern_statistics_pattern_id", table_name="pattern_statistics")
    op.drop_table("pattern_statistics")
    op.drop_index("ix_event_fingerprints_confidence_score", table_name="event_fingerprints")
    op.drop_index("ix_event_fingerprints_direction", table_name="event_fingerprints")
    op.drop_index("ix_event_fingerprints_event_id", table_name="event_fingerprints")
    op.drop_table("event_fingerprints")
    op.drop_index("ix_market_memory_records_confidence_score", table_name="market_memory_records")
    op.drop_index("ix_market_memory_records_memory_score", table_name="market_memory_records")
    op.drop_index("ix_market_memory_records_memory_type", table_name="market_memory_records")
    op.drop_index("ix_market_memory_records_pattern_id", table_name="market_memory_records")
    op.drop_index("ix_market_memory_records_event_id", table_name="market_memory_records")
    op.drop_table("market_memory_records")
