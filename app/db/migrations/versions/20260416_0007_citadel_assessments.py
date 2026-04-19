"""add citadel assessments table

Revision ID: 20260416_0007
Revises: 20260414_0006
Create Date: 2026-04-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_0007"
down_revision = "20260414_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "citadel_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_type", sa.String(length=40), nullable=False, server_default="user"),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("custody_resilience_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recovery_readiness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("privacy_resilience_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("treasury_resilience_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("vendor_independence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("inheritance_readiness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fee_survivability_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("policy_maturity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("operational_hygiene_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("critical_findings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("warnings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("recommendations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("freshness_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_citadel_assessments_owner_type", "citadel_assessments", ["owner_type"], unique=False)
    op.create_index("ix_citadel_assessments_owner_id", "citadel_assessments", ["owner_id"], unique=False)
    op.create_index("ix_citadel_assessments_generated_at", "citadel_assessments", ["generated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_citadel_assessments_generated_at", table_name="citadel_assessments")
    op.drop_index("ix_citadel_assessments_owner_id", table_name="citadel_assessments")
    op.drop_index("ix_citadel_assessments_owner_type", table_name="citadel_assessments")
    op.drop_table("citadel_assessments")
