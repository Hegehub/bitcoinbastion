"""durable operations incidents and transition history

Revision ID: 20260811_0072
Revises: 20260727_0071
"""
from alembic import op
import sqlalchemy as sa
revision = "20260811_0072"
down_revision = "20260727_0071"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("operations_incidents",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("incident_id", sa.String(36), nullable=False),
        sa.Column("correlation_key", sa.String(320), nullable=False), sa.Column("active_correlation_key", sa.String(320), nullable=True),
        sa.Column("detector_id", sa.String(120), nullable=False), sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("affected_target", sa.String(200), nullable=False), sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("source", sa.String(160), nullable=False), sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("incident_id"), sa.UniqueConstraint("active_correlation_key", name="uq_operations_incident_active_correlation"))
    for name, cols in (("ix_operations_incident_id", ["incident_id"]),("ix_operations_incident_status",["status"]),("ix_operations_incident_severity",["severity"]),("ix_operations_incident_target",["affected_target"]),("ix_operations_incident_correlation",["correlation_key"])):
        op.create_index(name,"operations_incidents",cols)
    op.create_table("operations_incident_transitions",
        sa.Column("id",sa.Integer(),primary_key=True), sa.Column("incident_id",sa.String(36),sa.ForeignKey("operations_incidents.incident_id"),nullable=False),
        sa.Column("transition",sa.String(30),nullable=False),sa.Column("status",sa.String(20),nullable=False),sa.Column("severity",sa.String(20),nullable=False),
        sa.Column("observed_at",sa.DateTime(),nullable=False),sa.Column("source",sa.String(160),nullable=False),sa.Column("summary",sa.String(500),nullable=False))
    op.create_index("ix_operations_transition_incident","operations_incident_transitions",["incident_id"])
    op.create_index("ix_operations_transition_observed","operations_incident_transitions",["observed_at"])

def downgrade() -> None:
    op.drop_table("operations_incident_transitions")
    op.drop_table("operations_incidents")
