"""harden webhook delivery logs

Revision ID: 20260608_0055
Revises: 20260608_0054
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "20260608_0055"
down_revision = "20260608_0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("webhook_endpoints", sa.Column("signing_secret", sa.Text(), nullable=True))
    op.add_column(
        "webhook_deliveries",
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "webhook_deliveries", sa.Column("request_body_hash", sa.String(length=64), nullable=True)
    )
    op.add_column("webhook_deliveries", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("webhook_deliveries", sa.Column("next_retry_at", sa.DateTime(), nullable=True))
    op.create_index("ix_webhook_deliveries_next_retry_at", "webhook_deliveries", ["next_retry_at"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_next_retry_at", table_name="webhook_deliveries")
    op.drop_column("webhook_deliveries", "next_retry_at")
    op.drop_column("webhook_deliveries", "duration_ms")
    op.drop_column("webhook_deliveries", "request_body_hash")
    op.drop_column("webhook_deliveries", "attempt_number")
    op.drop_column("webhook_endpoints", "signing_secret")
