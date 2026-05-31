"""source registry expansion

Revision ID: 20260526_0016
Revises: 20260526_0015
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0016"
down_revision = "20260526_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_sources", sa.Column("homepage_url", sa.String(length=512), nullable=False, server_default=""))
    op.add_column("news_sources", sa.Column("country_code", sa.String(length=3), nullable=True))
    op.add_column("news_sources", sa.Column("signal_quality_weight", sa.Float(), nullable=False, server_default="0.7"))
    op.add_column("news_sources", sa.Column("sovereignty_weight", sa.Float(), nullable=False, server_default="0.7"))
    op.add_column("news_sources", sa.Column("default_confidence", sa.Float(), nullable=False, server_default="0.7"))
    op.add_column("news_sources", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("news_sources", sa.Column("requires_js_rendering", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_sources", sa.Column("request_timeout_seconds", sa.Integer(), nullable=False, server_default="15"))
    op.add_column("news_sources", sa.Column("backoff_multiplier", sa.Float(), nullable=False, server_default="2.0"))
    op.add_column("news_sources", sa.Column("max_failures_before_backoff", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("news_sources", sa.Column("tags_json", sa.JSON(), nullable=False, server_default="[]"))
    op.create_index("ix_news_sources_created_at", "news_sources", ["created_at"])
    op.create_table("source_health_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("http_status_code", sa.Integer(), nullable=True), sa.Column("latency_ms", sa.Integer(), nullable=True), sa.Column("response_size_bytes", sa.Integer(), nullable=True), sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("backoff_until", sa.DateTime(), nullable=True), sa.Column("last_error", sa.String(1000), nullable=False, server_default=""), sa.Column("etag", sa.String(255), nullable=False, server_default=""), sa.Column("last_modified", sa.String(255), nullable=False, server_default=""), sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"), sa.Column("health_score", sa.Float(), nullable=False, server_default="0"), sa.Column("checked_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS source_health_records")
    op.drop_index("ix_news_sources_created_at", table_name="news_sources")
    for c in ["tags_json", "max_failures_before_backoff", "backoff_multiplier", "request_timeout_seconds", "requires_js_rendering", "is_public", "default_confidence", "sovereignty_weight", "signal_quality_weight", "country_code", "homepage_url"]:
        op.drop_column("news_sources", c)
