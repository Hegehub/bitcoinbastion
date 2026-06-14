"""add event outbox

Revision ID: 20260607_0053
Revises: 20260605_0052
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "20260607_0053"
down_revision = "20260605_0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("domain", sa.String(length=80), nullable=False),
        sa.Column("aggregate_type", sa.String(length=120), nullable=True),
        sa.Column("aggregate_id", sa.String(length=160), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("locked_by", sa.String(length=120), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_event_outbox_event_id", "event_outbox", ["event_id"], unique=True)
    op.create_index("ix_event_outbox_status", "event_outbox", ["status"])
    op.create_index("ix_event_outbox_event_type", "event_outbox", ["event_type"])
    op.create_index("ix_event_outbox_domain", "event_outbox", ["domain"])
    op.create_index(
        "ix_event_outbox_aggregate", "event_outbox", ["aggregate_type", "aggregate_id"]
    )
    op.create_index("ix_event_outbox_next_attempt_at", "event_outbox", ["next_attempt_at"])
    op.create_index("ix_event_outbox_created_at", "event_outbox", ["created_at"])
    op.create_index(
        "ix_event_outbox_status_next_attempt", "event_outbox", ["status", "next_attempt_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_event_outbox_status_next_attempt", table_name="event_outbox")
    op.drop_index("ix_event_outbox_created_at", table_name="event_outbox")
    op.drop_index("ix_event_outbox_next_attempt_at", table_name="event_outbox")
    op.drop_index("ix_event_outbox_aggregate", table_name="event_outbox")
    op.drop_index("ix_event_outbox_domain", table_name="event_outbox")
    op.drop_index("ix_event_outbox_event_type", table_name="event_outbox")
    op.drop_index("ix_event_outbox_status", table_name="event_outbox")
    op.drop_index("ix_event_outbox_event_id", table_name="event_outbox")
    op.drop_table("event_outbox")
