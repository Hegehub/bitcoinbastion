"""add source reputation profiles

Revision ID: 20260414_0005
Revises: 20260414_0004
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0005"
down_revision = "20260414_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_reputation_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consistency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("signal_quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_source_reputation_profiles_source_id",
        "source_reputation_profiles",
        ["source_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_source_reputation_profiles_source_id", table_name="source_reputation_profiles")
    op.drop_table("source_reputation_profiles")
