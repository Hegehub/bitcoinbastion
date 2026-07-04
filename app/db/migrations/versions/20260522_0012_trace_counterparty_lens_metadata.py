"""trace counterparty lens metadata

Revision ID: 20260522_0012
Revises: 20260522_0011
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

revision = "20260522_0012"
down_revision = "20260522_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trace_reports",
        sa.Column("counterparty_lens_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("trace_reports", "counterparty_lens_json")
