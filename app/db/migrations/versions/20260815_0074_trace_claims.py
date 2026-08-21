"""add immutable Trace analytical claims

Revision ID: 20260815_0074
Revises: 20260812_0073
"""

from alembic import op
import sqlalchemy as sa

revision = "20260815_0074"
down_revision = "20260812_0073"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trace_claims",
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=False),
        sa.Column("capture_id", sa.String(64), nullable=False),
        sa.Column("claim_schema_version", sa.String(64), nullable=False),
        sa.Column("subject_kind", sa.String(64), nullable=False),
        sa.Column("subject_id", sa.String(96), nullable=False),
        sa.Column("subject_public_value", sa.String(256), nullable=False),
        sa.Column("predicate", sa.String(64), nullable=False),
        sa.Column("value_kind", sa.String(64), nullable=False),
        sa.Column("value_text", sa.String(128), nullable=False),
        sa.Column("producer_id", sa.String(128), nullable=False),
        sa.Column("producer_version", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("input_references_json", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, columns in (
        ("ix_trace_claims_report_id", ["report_id"]),
        ("ix_trace_claims_capture_id", ["capture_id"]),
        ("ix_trace_claims_subject_id", ["subject_id"]),
        ("ix_trace_claims_predicate", ["predicate"]),
        ("ix_trace_claims_producer_id", ["producer_id"]),
        ("ix_trace_claims_source_id", ["source_id"]),
    ):
        op.create_index(name, "trace_claims", columns)


def downgrade() -> None:
    op.drop_table("trace_claims")
