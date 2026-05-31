"""news scoring engine

Revision ID: 20260527_0026
Revises: 20260527_0025
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0026"
down_revision = "20260527_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("urgency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_credibility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("institutional_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("macro_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("regulatory_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("security_risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sovereignty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("novelty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("score_version", sa.String(length=16), nullable=False, server_default="v1"),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.Column("factor_breakdown_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("high_uncertainty", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provider_disagreement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stale_evidence", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("low_confidence", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_news_scores_article_id", "news_scores", ["article_id"])
    op.create_index("ix_news_scores_event_id", "news_scores", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_news_scores_event_id", table_name="news_scores")
    op.drop_index("ix_news_scores_article_id", table_name="news_scores")
    op.drop_table("news_scores")
