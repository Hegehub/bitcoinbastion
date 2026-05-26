"""source health + provider confidence engine tables

Revision ID: 20260526_0017
Revises: 20260526_0016
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from typing import Any

revision = "20260526_0017"
down_revision = "20260526_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    cols: list[Any] = [
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.50"),
        sa.Column("backoff_until", sa.DateTime(), nullable=True),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("health_band", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("etag", sa.String(255), nullable=True),
        sa.Column("last_modified", sa.String(255), nullable=True),
        sa.Column("last_content_hash", sa.String(64), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
     ]
    for col in cols:
        op.add_column("news_sources", col)

    op.execute("DROP TABLE IF EXISTS source_health_records")
    op.create_table(
        "source_health_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False),
        sa.Column("check_started_at", sa.DateTime(), nullable=False),
        sa.Column("check_finished_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_type", sa.String(32), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("response_size_bytes", sa.Integer(), nullable=True),
        sa.Column("etag", sa.String(255), nullable=True),
        sa.Column("last_modified", sa.String(255), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("provider_confidence_before", sa.Float(), nullable=False),
        sa.Column("provider_confidence_after", sa.Float(), nullable=False),
        sa.Column("failure_count_snapshot", sa.Integer(), nullable=False),
        sa.Column("success_count_snapshot", sa.Integer(), nullable=False),
        sa.Column("backoff_until", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table("source_health_snapshots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False), sa.Column("snapshot_window", sa.String(16), nullable=False), sa.Column("success_rate", sa.Float(), nullable=False), sa.Column("failure_rate", sa.Float(), nullable=False), sa.Column("avg_latency_ms", sa.Float(), nullable=True), sa.Column("median_latency_ms", sa.Float(), nullable=True), sa.Column("p95_latency_ms", sa.Float(), nullable=True), sa.Column("provider_confidence", sa.Float(), nullable=False), sa.Column("consecutive_failures", sa.Integer(), nullable=False), sa.Column("consecutive_successes", sa.Integer(), nullable=False), sa.Column("last_success_at", sa.DateTime(), nullable=True), sa.Column("last_failure_at", sa.DateTime(), nullable=True), sa.Column("degraded_state", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("health_band", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_table("provider_confidence_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False), sa.Column("event_type", sa.String(32), nullable=False), sa.Column("old_confidence", sa.Float(), nullable=False), sa.Column("new_confidence", sa.Float(), nullable=False), sa.Column("delta", sa.Float(), nullable=False), sa.Column("reason_code", sa.String(64), nullable=False), sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    op.drop_table("provider_confidence_events")
    op.drop_table("source_health_snapshots")
    op.execute("DROP TABLE IF EXISTS source_health_records")
    for c in ["last_checked_at", "last_content_hash", "last_modified", "etag", "last_error", "health_band", "is_degraded", "backoff_until", "provider_confidence", "avg_latency_ms", "consecutive_successes", "consecutive_failures", "success_count", "failure_count", "last_status_code"]:
        op.drop_column("news_sources", c)
