"""bastion trace initial tables

Revision ID: 20260522_0009
Revises: 20260430_0008
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

revision = "20260522_0009"
down_revision = "20260430_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trace_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.String(length=128), nullable=False),
        sa.Column("chain", sa.String(length=32), nullable=False),
        sa.Column("trace_score", sa.Float(), nullable=False),
        sa.Column("trace_band", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_quality", sa.String(length=32), nullable=False),
        sa.Column("freshness", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("operator_guidance_json", sa.Text(), nullable=False),
        sa.Column("reason_codes_json", sa.Text(), nullable=False),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False),
        sa.Column("advisory_not_legal_verdict", sa.Boolean(), nullable=False),
        sa.Column("not_consensus_proof", sa.Boolean(), nullable=False),
        sa.Column("no_custody", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trace_reports_address", "trace_reports", ["address"])

    op.create_table(
        "trace_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("trust_level", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("source_name"),
    )

    op.create_table(
        "trace_source_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("trace_sources.id"), nullable=False),
        sa.Column("last_refreshed_at", sa.DateTime(), nullable=False),
        sa.Column("freshness", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("last_refresh_status", sa.String(length=64), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trace_source_snapshots_source_id", "trace_source_snapshots", ["source_id"])

    op.create_table(
        "trace_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("trace_reports.id"), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("freshness_days", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("evidence_ref", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trace_evidence_report_id", "trace_evidence", ["report_id"])

    op.create_table(
        "trace_watchlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("risk_hint", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trace_watchlist_entries_address", "trace_watchlist_entries", ["address"])


def downgrade() -> None:
    op.drop_index("ix_trace_watchlist_entries_address", table_name="trace_watchlist_entries")
    op.drop_table("trace_watchlist_entries")
    op.drop_index("ix_trace_evidence_report_id", table_name="trace_evidence")
    op.drop_table("trace_evidence")
    op.drop_index("ix_trace_source_snapshots_source_id", table_name="trace_source_snapshots")
    op.drop_table("trace_source_snapshots")
    op.drop_table("trace_sources")
    op.drop_index("ix_trace_reports_address", table_name="trace_reports")
    op.drop_table("trace_reports")
