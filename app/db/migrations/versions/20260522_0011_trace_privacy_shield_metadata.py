"""trace privacy shield metadata

Revision ID: 20260522_0011
Revises: 20260522_0010
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = "20260522_0011"
down_revision = "20260522_0010"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("trace_reports", sa.Column("privacy_shield_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("utxo_hygiene_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("dust_radar_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("address_reuse_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("consolidation_risk_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("trace_reports", sa.Column("toxic_change_json", sa.Text(), nullable=False, server_default="{}"))

def downgrade() -> None:
    op.drop_column("trace_reports", "toxic_change_json")
    op.drop_column("trace_reports", "consolidation_risk_json")
    op.drop_column("trace_reports", "address_reuse_json")
    op.drop_column("trace_reports", "dust_radar_json")
    op.drop_column("trace_reports", "utxo_hygiene_json")
    op.drop_column("trace_reports", "privacy_shield_json")
