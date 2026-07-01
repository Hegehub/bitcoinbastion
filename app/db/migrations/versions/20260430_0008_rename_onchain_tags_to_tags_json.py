"""drop legacy onchain tags column

Revision ID: 20260430_0008
Revises: 9ecab5c090cf
Create Date: 2026-04-30 12:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260430_0008"
down_revision = "9ecab5c090cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("onchain_events") as batch_op:
        batch_op.drop_column("tags")


def downgrade() -> None:
    with op.batch_alter_table("onchain_events") as batch_op:
        batch_op.add_column(
            sa.Column("tags", sa.String(length=255), nullable=False, server_default="")
        )
