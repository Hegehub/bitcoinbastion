"""trace origin/source metadata

Revision ID: 20260522_0010
Revises: 20260522_0009
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

revision = "20260522_0010"
down_revision = "20260522_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trace_reports", sa.Column("origin_passport_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("provider_disagreement_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("evidence_independence_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("source_status_summary_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("trace_reports", "source_status_summary_json")
    op.drop_column("trace_reports", "evidence_independence_json")
    op.drop_column("trace_reports", "provider_disagreement_json")
    op.drop_column("trace_reports", "origin_passport_json")
