"""news ingestion foundation

Revision ID: 20260526_0015
Revises: 20260526_0014
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from typing import Any

revision = "20260526_0015"
down_revision = "20260526_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns: list[Any] = [
        sa.Column("raw_url", sa.String(2048), nullable=False, server_default=""),
        sa.Column("raw_content", sa.Text(), nullable=False, server_default=""),
        sa.Column("discovered_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ingestion_method", sa.String(32), nullable=False, server_default="RSS"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("fetch_status", sa.String(32), nullable=False, server_default="fetched"),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("etag", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_modified", sa.String(255), nullable=False, server_default=""),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(120), nullable=False, server_default=""),
        sa.Column(
            "is_duplicate_candidate", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("duplicate_candidate_reason", sa.String(120), nullable=False, server_default=""),
    ]
    for col in columns:
        op.add_column("news_articles", col)
    op.create_index("ix_news_articles_fetched_at", "news_articles", ["fetched_at"])
    op.create_table(
        "news_fetch_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("items_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_duplicate_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(1000), nullable=False, server_default=""),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("etag_used", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_modified_used", sa.String(255), nullable=False, server_default=""),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "news_raw_payloads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("payload_format", sa.String(32), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("compression", sa.String(32), nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("news_raw_payloads")
    op.drop_table("news_fetch_logs")
