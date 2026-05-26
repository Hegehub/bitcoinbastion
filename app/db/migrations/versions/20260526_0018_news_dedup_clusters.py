"""news deduplication and clustering engine schema

Revision ID: 20260526_0018
Revises: 20260526_0017
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from typing import Any

revision = "20260526_0018"
down_revision = "20260526_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_article_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(128), nullable=False),
        sa.Column("canonical_article_id", sa.Integer(), nullable=True),
        sa.Column("cluster_type", sa.String(32), nullable=False, server_default="topic"),
        sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("cluster_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cluster_summary", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_article_clusters_cluster_key", "news_article_clusters", ["cluster_key"], unique=True)
    cols: list[Any] = [
        sa.Column("normalized_title_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("deduplication_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("is_canonical", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deduplication_reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("deduplication_metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    ]
    for col in cols:
        op.add_column("news_articles", col)
    op.create_index("ix_news_articles_duplicate_of_id", "news_articles", ["duplicate_of_id"])
    op.create_index("ix_news_articles_cluster_id", "news_articles", ["cluster_id"])
    op.create_index("ix_news_articles_normalized_title_hash", "news_articles", ["normalized_title_hash"])


def downgrade() -> None:
    op.drop_index("ix_news_articles_normalized_title_hash", table_name="news_articles")
    op.drop_index("ix_news_articles_cluster_id", table_name="news_articles")
    op.drop_index("ix_news_articles_duplicate_of_id", table_name="news_articles")
    for c in ["deduplication_metadata_json", "deduplication_reason", "is_canonical", "cluster_id", "similarity_score", "deduplication_status", "normalized_title_hash"]:
        op.drop_column("news_articles", c)
    op.drop_index("ix_news_article_clusters_cluster_key", table_name="news_article_clusters")
    op.drop_table("news_article_clusters")
