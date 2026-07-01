"""trace business tier baseline

Revision ID: 20260522_0013
Revises: 20260522_0012
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

revision = "20260522_0013"
down_revision = "20260522_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trace_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_label", sa.String(120), nullable=False, server_default=""),
        sa.Column("business_context", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("policy_profile_id", sa.String(64), nullable=True),
        sa.Column("total_addresses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unknown_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manual_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_batch_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("trace_batches.id"), nullable=False),
        sa.Column("address", sa.String(128), nullable=False),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="processed"),
        sa.Column("rejection_reason", sa.String(128), nullable=True),
        sa.Column("trace_band", sa.String(32), nullable=True),
        sa.Column("trace_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("policy_action", sa.String(64), nullable=True),
        sa.Column(
            "manual_review_recommended",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_business_policy_profiles",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("context_type", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("low_action", sa.String(64), nullable=False, server_default="ACCEPT"),
        sa.Column("medium_action", sa.String(64), nullable=False, server_default="HOLD_FOR_REVIEW"),
        sa.Column("high_action", sa.String(64), nullable=False, server_default="HOLD_FOR_REVIEW"),
        sa.Column(
            "critical_action", sa.String(64), nullable=False, server_default="REJECT_BY_POLICY"
        ),
        sa.Column(
            "unknown_action",
            sa.String(64),
            nullable=False,
            server_default="INSUFFICIENT_INFORMATION",
        ),
        sa.Column(
            "manual_review_threshold", sa.String(32), nullable=False, server_default="MEDIUM"
        ),
        sa.Column(
            "high_value_threshold_sats", sa.Integer(), nullable=False, server_default="5000000"
        ),
        sa.Column(
            "require_review_on_provider_disagreement",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "require_review_on_low_confidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "require_review_on_privacy_high",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_review_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("trace_batches.id"), nullable=True),
        sa.Column("address", sa.String(128), nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("review_priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("assigned_to", sa.String(120), nullable=True),
        sa.Column("operator_note_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(64), nullable=False, server_default="NO_DECISION"),
        sa.Column("decision_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "trace_operator_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "review_item_id", sa.Integer(), sa.ForeignKey("trace_review_items.id"), nullable=True
        ),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=True),
        sa.Column("note_type", sa.String(64), nullable=False, server_default="GENERAL"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", sa.String(120), nullable=True),
        sa.Column("redacted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_business_proof_packets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=False),
        sa.Column(
            "review_item_id", sa.Integer(), sa.ForeignKey("trace_review_items.id"), nullable=True
        ),
        sa.Column("policy_profile_id", sa.String(64), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_business_exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("trace_batches.id"), nullable=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=True),
        sa.Column("format", sa.String(32), nullable=False, server_default="JSON"),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("payload_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "trace_business_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trace_business_events")
    op.drop_table("trace_business_exports")
    op.drop_table("trace_business_proof_packets")
    op.drop_table("trace_operator_notes")
    op.drop_table("trace_review_items")
    op.drop_table("trace_business_policy_profiles")
    op.drop_table("trace_batch_items")
    op.drop_table("trace_batches")
