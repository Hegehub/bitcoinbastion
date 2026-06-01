"""news narrative tags

Revision ID: 20260527_0028
Revises: 20260527_0027
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0028"
down_revision = "20260527_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_narrative_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_keywords_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_news_narrative_tags_article_id", "news_narrative_tags", ["article_id"])
    op.create_index("ix_news_narrative_tags_event_id", "news_narrative_tags", ["event_id"])
    op.create_index("ix_news_narrative_tags_tag", "news_narrative_tags", ["tag"])


def downgrade() -> None:
    op.drop_index("ix_news_narrative_tags_tag", table_name="news_narrative_tags")
    op.drop_index("ix_news_narrative_tags_event_id", table_name="news_narrative_tags")
    op.drop_index("ix_news_narrative_tags_article_id", table_name="news_narrative_tags")
    op.drop_table("news_narrative_tags")
