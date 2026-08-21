"""add immutable Trace Graph snapshots

Revision ID: 20260815_0075
Revises: 20260815_0074
"""

from alembic import op
import sqlalchemy as sa

revision = "20260815_0075"
down_revision = "20260815_0074"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trace_graph_snapshots",
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=False),
        sa.Column("topology_snapshot_id", sa.String(96), nullable=False),
        sa.Column("claim_capture_id", sa.String(64), nullable=False),
        sa.Column("snapshot_schema_version", sa.String(64), nullable=False),
        sa.Column("graph_version", sa.String(64), nullable=False),
        sa.Column("builder_version", sa.String(64), nullable=False),
        sa.Column("graph_digest", sa.String(64), nullable=False),
        sa.Column("graph_payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "report_id", "topology_snapshot_id", "builder_version", name="uq_trace_graph_capture"
        ),
    )
    for name, columns in (
        ("ix_trace_graph_snapshots_report_id", ["report_id"]),
        ("ix_trace_graph_snapshots_topology_snapshot_id", ["topology_snapshot_id"]),
        ("ix_trace_graph_snapshots_claim_capture_id", ["claim_capture_id"]),
    ):
        op.create_index(name, "trace_graph_snapshots", columns)


def downgrade() -> None:
    op.drop_table("trace_graph_snapshots")
