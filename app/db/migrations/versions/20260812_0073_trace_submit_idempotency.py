"""add durable Trace submit idempotency

Revision ID: 20260812_0073
Revises: 20260811_0072
"""

from alembic import op
import sqlalchemy as sa

revision = "20260812_0073"
down_revision = "20260811_0072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trace_reports", sa.Column("idempotency_key_hash", sa.String(64), nullable=True))
    with op.batch_alter_table("trace_reports") as batch_op:
        batch_op.create_unique_constraint(
            "uq_trace_reports_idempotency_key_hash", ["idempotency_key_hash"]
        )


def downgrade() -> None:
    with op.batch_alter_table("trace_reports") as batch_op:
        batch_op.drop_constraint("uq_trace_reports_idempotency_key_hash", type_="unique")
    op.drop_column("trace_reports", "idempotency_key_hash")
