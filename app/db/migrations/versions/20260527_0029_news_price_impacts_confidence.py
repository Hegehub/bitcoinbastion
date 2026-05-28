"""news price impacts confidence diagnostics

Revision ID: 20260527_0029
Revises: 20260527_0028
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0029"
down_revision = "20260527_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_price_impacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_band", sa.String(length=16), nullable=False, server_default="very_low"),
        sa.Column("confidence_contributions_json", sa.JSON(), nullable=False),
        sa.Column("degradation_factors_json", sa.JSON(), nullable=False),
        sa.Column("uncertainty_flags_json", sa.JSON(), nullable=False),
        sa.Column("delayed_reaction_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("false_signal_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("freshness_weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("volatility_context_weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("event_confirmation_weight", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("explanation_summary", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("limitation", sa.String(length=200), nullable=False, server_default="Correlation-based attribution is not proof of causation."),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_news_price_impacts_article_id", "news_price_impacts", ["article_id"])


def downgrade() -> None:
    op.drop_index("ix_news_price_impacts_article_id", table_name="news_price_impacts")
    op.drop_table("news_price_impacts")
