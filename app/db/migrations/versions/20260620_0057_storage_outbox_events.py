"""create storage outbox events table

Revision ID: 20260620_0057
Revises: 20260619_0056
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa

revision = "20260620_0057"
down_revision = "20260619_0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("aggregate_type", sa.String(length=120), nullable=False),
        sa.Column("aggregate_id", sa.String(length=160), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("target_stores", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("locked_by", sa.String(length=160), nullable=True),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("available_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", name="uq_storage_outbox_events_event_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_storage_outbox_events_idempotency_key"),
    )
    op.create_index(
        "ix_storage_outbox_status_available_at",
        "storage_outbox_events",
        ["status", "available_at"],
    )
    op.create_index("ix_storage_outbox_event_type", "storage_outbox_events", ["event_type"])
    op.create_index(
        "ix_storage_outbox_aggregate",
        "storage_outbox_events",
        ["aggregate_type", "aggregate_id"],
    )
    op.create_index("ix_storage_outbox_created_at", "storage_outbox_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_storage_outbox_created_at", table_name="storage_outbox_events")
    op.drop_index("ix_storage_outbox_aggregate", table_name="storage_outbox_events")
    op.drop_index("ix_storage_outbox_event_type", table_name="storage_outbox_events")
    op.drop_index("ix_storage_outbox_status_available_at", table_name="storage_outbox_events")
    op.drop_table("storage_outbox_events")
