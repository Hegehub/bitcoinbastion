"""market intelligence foundation tables

Revision ID: 20260526_0014
Revises: 20260522_0013
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0014"
down_revision = "20260522_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("canonical_title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "primary_article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True
        ),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("article_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("event_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_label", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_events_event_type", "news_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_news_events_event_type", table_name="news_events")
    op.drop_table("news_events")
