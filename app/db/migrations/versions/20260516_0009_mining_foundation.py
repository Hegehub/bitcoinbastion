"""mining persistence foundation

Revision ID: 20260516_0009
Revises: 20260430_0008
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260516_0009"
down_revision = "20260430_0008"
branch_labels = None
depends_on = None


def _drop_index_if_exists(name: str, table: str) -> None:
    bind = op.get_bind()
    table_names = set(inspect(bind).get_table_names())
    existing = {idx["name"] for idx in inspect(bind).get_indexes(table)} if table in table_names else set()
    if name in existing:
        op.drop_index(name, table_name=table)


def _drop_table_if_exists(name: str) -> None:
    bind = op.get_bind()
    if name in set(inspect(bind).get_table_names()):
        op.drop_table(name)


def upgrade() -> None:
    op.create_table(
        "mining_pools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False, server_default="unknown"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mining_pool_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=False),
        sa.Column("endpoint_type", sa.String(length=40), nullable=False, server_default="api"),
        sa.Column("endpoint_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("network", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "stratum_v2_capabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=False),
        sa.Column("capability_state", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("job_declaration_state", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("translator_proxy_state", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("encrypted_channel_state", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "pool_sovereignty_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=False),
        sa.Column("score_100", sa.Float(), nullable=False, server_default="0"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("factor_breakdown_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("window_start", sa.DateTime(), nullable=True),
        sa.Column("window_end", sa.DateTime(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mining_censorship_risks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=False),
        sa.Column("risk_score_100", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("factor_breakdown_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("window_start", sa.DateTime(), nullable=True),
        sa.Column("window_end", sa.DateTime(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "template_control_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=False),
        sa.Column("template_control_state", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("template_control_owner", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("template_sovereignty_score_100", sa.Float(), nullable=False, server_default="0"),
        sa.Column("template_interference_risk_score_100", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mitm_risk_level", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mining_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("mining_pools.id"), nullable=True),
        sa.Column("signal_type", sa.String(length=60), nullable=False, server_default="MINING_SOVEREIGNTY"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="unknown"),
        sa.Column("provider_name", sa.String(length=120), nullable=False, server_default="unknown"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("freshness_seconds", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("evidence_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_mining_pool_endpoints_pool_id", "mining_pool_endpoints", ["pool_id"])
    op.create_index("ix_stratum_v2_capabilities_pool_id", "stratum_v2_capabilities", ["pool_id"])
    op.create_index("ix_pool_sovereignty_scores_pool_id", "pool_sovereignty_scores", ["pool_id"])
    op.create_index("ix_mining_censorship_risks_pool_id", "mining_censorship_risks", ["pool_id"])
    op.create_index("ix_template_control_assessments_pool_id", "template_control_assessments", ["pool_id"])
    op.create_index("ix_mining_signals_pool_id", "mining_signals", ["pool_id"])


def downgrade() -> None:
    _drop_index_if_exists("ix_mining_signals_pool_id", "mining_signals")
    _drop_index_if_exists("ix_template_control_assessments_pool_id", "template_control_assessments")
    _drop_index_if_exists("ix_mining_censorship_risks_pool_id", "mining_censorship_risks")
    _drop_index_if_exists("ix_pool_sovereignty_scores_pool_id", "pool_sovereignty_scores")
    _drop_index_if_exists("ix_stratum_v2_capabilities_pool_id", "stratum_v2_capabilities")
    _drop_index_if_exists("ix_mining_pool_endpoints_pool_id", "mining_pool_endpoints")

    _drop_table_if_exists("mining_signals")
    _drop_table_if_exists("template_control_assessments")
    _drop_table_if_exists("mining_censorship_risks")
    _drop_table_if_exists("pool_sovereignty_scores")
    _drop_table_if_exists("stratum_v2_capabilities")
    _drop_table_if_exists("mining_pool_endpoints")
    _drop_table_if_exists("mining_pools")
