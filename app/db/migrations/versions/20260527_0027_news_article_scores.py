"""news article scores table

Revision ID: 20260527_0027
Revises: 20260527_0026
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0027"
down_revision = "20260527_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_article_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=False),
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
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_label", sa.String(length=16), nullable=False, server_default="UNCERTAIN"),
        sa.Column("risk_band", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
        sa.Column("score_version", sa.String(length=32), nullable=False, server_default="v1_rule_based"),
        sa.Column("scoring_method", sa.String(length=32), nullable=False, server_default="RULE_BASED"),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.Column("factor_breakdown_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_news_article_scores_article_id", "news_article_scores", ["article_id"])
    op.create_index("ix_news_article_scores_event_id", "news_article_scores", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_news_article_scores_event_id", table_name="news_article_scores")
    op.drop_index("ix_news_article_scores_article_id", table_name="news_article_scores")
    op.drop_table("news_article_scores")
