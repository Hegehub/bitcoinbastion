"""operations evidence and slo control plane

Revision ID: 20260605_0050
Revises: 20260527_0049
Create Date: 2026-06-05 00:50:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260605_0050"
down_revision = "20260527_0049"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "operations_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("drill_id", sa.String(length=120), nullable=False),
        sa.Column("drill_type", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("operator", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("artifact_refs", json_type, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_operations_evidence_drill_id", "operations_evidence", ["drill_id"])
    op.create_index("ix_operations_evidence_drill_type", "operations_evidence", ["drill_type"])
    op.create_index("ix_operations_evidence_started_at", "operations_evidence", ["started_at"])
    op.create_index("ix_operations_evidence_success", "operations_evidence", ["success"])
    op.create_index("ix_operations_evidence_created_at", "operations_evidence", ["created_at"])

    op.create_table(
        "operations_slo_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slo_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("target", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("observed_value", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("window", sa.String(length=32), nullable=False, server_default="24h"),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("operational_limitations", json_type, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_operations_slo_snapshots_slo_name", "operations_slo_snapshots", ["slo_name"])
    op.create_index("ix_operations_slo_snapshots_status", "operations_slo_snapshots", ["status"])
    op.create_index("ix_operations_slo_snapshots_created_at", "operations_slo_snapshots", ["created_at"])


def downgrade() -> None:
    for index in ["ix_operations_slo_snapshots_created_at", "ix_operations_slo_snapshots_status", "ix_operations_slo_snapshots_slo_name"]:
        op.drop_index(index, table_name="operations_slo_snapshots")
    op.drop_table("operations_slo_snapshots")
    for index in [
        "ix_operations_evidence_created_at",
        "ix_operations_evidence_success",
        "ix_operations_evidence_started_at",
        "ix_operations_evidence_drill_type",
        "ix_operations_evidence_drill_id",
    ]:
        op.drop_index(index, table_name="operations_evidence")
    op.drop_table("operations_evidence")
