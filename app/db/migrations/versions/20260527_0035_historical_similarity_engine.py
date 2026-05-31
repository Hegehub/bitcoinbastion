"""historical similarity engine

Revision ID: 20260527_0035
Revises: 20260527_0034
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0035"
down_revision = "20260527_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "historical_event_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("pattern_type", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("canonical_title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("primary_narrative", sa.String(length=128), nullable=False, server_default="unknown"),
        sa.Column("sentiment_label", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("institutional_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("macro_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("security_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("regulatory_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sovereignty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_change_15m_pct", sa.Float(), nullable=True),
        sa.Column("price_change_1h_pct", sa.Float(), nullable=True),
        sa.Column("price_change_4h_pct", sa.Float(), nullable=True),
        sa.Column("price_change_24h_pct", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for column_name in ["event_type", "pattern_type", "event_id", "article_id", "created_at"]:
        op.create_index(f"ix_historical_event_profiles_{column_name}", "historical_event_profiles", [column_name])

    op.create_table(
        "historical_similarity_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("candidate_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("narrative_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_behavior_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_window_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for column_name in ["reference_event_id", "candidate_event_id", "similarity_score"]:
        op.create_index(f"ix_historical_similarity_results_{column_name}", "historical_similarity_results", [column_name])


def downgrade() -> None:
    for column_name in ["similarity_score", "candidate_event_id", "reference_event_id"]:
        op.drop_index(f"ix_historical_similarity_results_{column_name}", table_name="historical_similarity_results")
    op.drop_table("historical_similarity_results")
    for column_name in ["created_at", "article_id", "event_id", "pattern_type", "event_type"]:
        op.drop_index(f"ix_historical_event_profiles_{column_name}", table_name="historical_event_profiles")
    op.drop_table("historical_event_profiles")
