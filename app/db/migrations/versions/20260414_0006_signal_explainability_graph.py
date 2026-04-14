"""add signal explainability graph tables

Revision ID: 20260414_0006
Revises: 20260414_0005
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0006"
down_revision = "20260414_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signal_explanations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("explanation_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence_reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("horizon", sa.String(length=40), nullable=False, server_default="short"),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_signal_explanations_signal_id", "signal_explanations", ["signal_id"], unique=False)

    op.create_table(
        "evidence_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("node_key", sa.String(length=120), nullable=False),
        sa.Column("node_type", sa.String(length=60), nullable=False, server_default="article"),
        sa.Column("label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_evidence_nodes_signal_id", "evidence_nodes", ["signal_id"], unique=False)
    op.create_index("ix_evidence_nodes_node_key", "evidence_nodes", ["node_key"], unique=False)

    op.create_table(
        "evidence_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("from_node_key", sa.String(length=120), nullable=False),
        sa.Column("to_node_key", sa.String(length=120), nullable=False),
        sa.Column("relation", sa.String(length=80), nullable=False, server_default="supports"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index("ix_evidence_edges_signal_id", "evidence_edges", ["signal_id"], unique=False)
    op.create_index("ix_evidence_edges_from_node_key", "evidence_edges", ["from_node_key"], unique=False)
    op.create_index("ix_evidence_edges_to_node_key", "evidence_edges", ["to_node_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_evidence_edges_to_node_key", table_name="evidence_edges")
    op.drop_index("ix_evidence_edges_from_node_key", table_name="evidence_edges")
    op.drop_index("ix_evidence_edges_signal_id", table_name="evidence_edges")
    op.drop_table("evidence_edges")

    op.drop_index("ix_evidence_nodes_node_key", table_name="evidence_nodes")
    op.drop_index("ix_evidence_nodes_signal_id", table_name="evidence_nodes")
    op.drop_table("evidence_nodes")

    op.drop_index("ix_signal_explanations_signal_id", table_name="signal_explanations")
    op.drop_table("signal_explanations")
