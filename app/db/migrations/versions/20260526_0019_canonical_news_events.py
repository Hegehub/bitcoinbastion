"""canonical news event engine schema

Revision ID: 20260526_0019
Revises: 20260526_0018
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0019"
down_revision = "20260526_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_events", sa.Column("event_key", sa.String(128), nullable=False, server_default=""))
    op.add_column("news_events", sa.Column("canonical_summary", sa.Text(), nullable=False, server_default=""))
    op.add_column("news_events", sa.Column("event_category", sa.String(64), nullable=False, server_default="unknown"))
    op.add_column("news_events", sa.Column("cluster_confidence", sa.Float(), nullable=False, server_default="0"))
    op.add_column("news_events", sa.Column("event_sentiment", sa.String(32), nullable=False, server_default="UNKNOWN"))
    op.add_column("news_events", sa.Column("first_source_id", sa.Integer(), nullable=True))
    op.add_column("news_events", sa.Column("first_source_name", sa.String(255), nullable=False, server_default=""))
    op.add_column("news_events", sa.Column("first_source_published_at", sa.DateTime(), nullable=True))
    op.add_column("news_events", sa.Column("dominant_language", sa.String(16), nullable=False, server_default="en"))
    op.add_column("news_events", sa.Column("is_high_impact", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_events", sa.Column("is_security_related", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_events", sa.Column("is_regulatory_related", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_events", sa.Column("is_macro_related", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_events", sa.Column("is_institutional_related", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_events", sa.Column("limitations_json", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index("ix_news_events_event_key", "news_events", ["event_key"])
    op.create_index("ix_news_events_event_category", "news_events", ["event_category"])

    op.create_table(
        "news_event_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=False),
        sa.Column("relationship_type", sa.String(64), nullable=False, server_default="supporting"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("is_primary_source", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("time_distance_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_event_articles_event_id", "news_event_articles", ["event_id"])
    op.create_index("ix_news_event_articles_article_id", "news_event_articles", ["article_id"])

    op.create_table(
        "news_event_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("cluster_hash", sa.String(128), nullable=False),
        sa.Column("cluster_strategy", sa.String(64), nullable=False, server_default="deterministic_v1"),
        sa.Column("cluster_reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_event_clusters_event_id", "news_event_clusters", ["event_id"])
    op.create_index("ix_news_event_clusters_cluster_hash", "news_event_clusters", ["cluster_hash"])


def downgrade() -> None:
    op.drop_index("ix_news_event_clusters_cluster_hash", table_name="news_event_clusters")
    op.drop_index("ix_news_event_clusters_event_id", table_name="news_event_clusters")
    op.drop_table("news_event_clusters")
    op.drop_index("ix_news_event_articles_article_id", table_name="news_event_articles")
    op.drop_index("ix_news_event_articles_event_id", table_name="news_event_articles")
    op.drop_table("news_event_articles")
    op.drop_index("ix_news_events_event_category", table_name="news_events")
    op.drop_index("ix_news_events_event_key", table_name="news_events")
    for col in ["limitations_json","is_institutional_related","is_macro_related","is_regulatory_related","is_security_related","is_high_impact","dominant_language","first_source_published_at","first_source_name","first_source_id","event_sentiment","cluster_confidence","event_category","canonical_summary","event_key"]:
        op.drop_column("news_events", col)
