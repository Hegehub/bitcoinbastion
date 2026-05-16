"""add mining sovereignty tables

Revision ID: 20260516_0010
Revises: 20260516_0009
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260516_0010"
down_revision = "20260516_0009"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in set(inspect(bind).get_table_names())


def _has_index(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    existing = {idx["name"] for idx in inspect(bind).get_indexes(table)}
    return index_name in existing


def _create_index_if_missing(index_name: str, table: str, columns: list[str]) -> None:
    if not _has_index(table, index_name):
        op.create_index(index_name, table, columns)


def _drop_index_if_exists(index_name: str, table: str) -> None:
    if _has_index(table, index_name):
        op.drop_index(index_name, table_name=table)


def upgrade() -> None:
    if not _has_table("mining_pools"):
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

    if not _has_table("mining_pool_endpoints"):
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

    if not _has_table("stratum_v2_capabilities"):
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

    if not _has_table("pool_sovereignty_scores"):
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

    if not _has_table("mining_censorship_risks"):
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

    if not _has_table("template_control_assessments"):
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

    if not _has_table("mining_signals"):
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

    # common query indexes
    _create_index_if_missing("ix_mining_pools_display_name", "mining_pools", ["display_name"])
    _create_index_if_missing("ix_mining_pools_observed_at", "mining_pools", ["observed_at"])
    _create_index_if_missing("ix_mining_pool_endpoints_pool_id", "mining_pool_endpoints", ["pool_id"])
    _create_index_if_missing("ix_mining_pool_endpoints_observed_at", "mining_pool_endpoints", ["observed_at"])
    _create_index_if_missing("ix_stratum_v2_capabilities_pool_id", "stratum_v2_capabilities", ["pool_id"])
    _create_index_if_missing("ix_stratum_v2_capabilities_observed_at", "stratum_v2_capabilities", ["observed_at"])
    _create_index_if_missing("ix_stratum_v2_capabilities_capability_state", "stratum_v2_capabilities", ["capability_state"])
    _create_index_if_missing("ix_pool_sovereignty_scores_pool_id", "pool_sovereignty_scores", ["pool_id"])
    _create_index_if_missing("ix_pool_sovereignty_scores_generated_at", "pool_sovereignty_scores", ["generated_at"])
    _create_index_if_missing("ix_mining_censorship_risks_pool_id", "mining_censorship_risks", ["pool_id"])
    _create_index_if_missing("ix_mining_censorship_risks_risk_level", "mining_censorship_risks", ["risk_level"])
    _create_index_if_missing("ix_mining_censorship_risks_generated_at", "mining_censorship_risks", ["generated_at"])
    _create_index_if_missing("ix_template_control_assessments_pool_id", "template_control_assessments", ["pool_id"])
    _create_index_if_missing("ix_template_control_assessments_observed_at", "template_control_assessments", ["observed_at"])
    _create_index_if_missing("ix_mining_signals_pool_id", "mining_signals", ["pool_id"])
    _create_index_if_missing("ix_mining_signals_observed_at", "mining_signals", ["observed_at"])


def downgrade() -> None:
    # drop indexes first when present
    _drop_index_if_exists("ix_mining_signals_observed_at", "mining_signals")
    _drop_index_if_exists("ix_mining_signals_pool_id", "mining_signals")
    _drop_index_if_exists("ix_template_control_assessments_observed_at", "template_control_assessments")
    _drop_index_if_exists("ix_template_control_assessments_pool_id", "template_control_assessments")
    _drop_index_if_exists("ix_mining_censorship_risks_generated_at", "mining_censorship_risks")
    _drop_index_if_exists("ix_mining_censorship_risks_risk_level", "mining_censorship_risks")
    _drop_index_if_exists("ix_mining_censorship_risks_pool_id", "mining_censorship_risks")
    _drop_index_if_exists("ix_pool_sovereignty_scores_generated_at", "pool_sovereignty_scores")
    _drop_index_if_exists("ix_pool_sovereignty_scores_pool_id", "pool_sovereignty_scores")
    _drop_index_if_exists("ix_stratum_v2_capabilities_capability_state", "stratum_v2_capabilities")
    _drop_index_if_exists("ix_stratum_v2_capabilities_pool_id", "stratum_v2_capabilities")
    _drop_index_if_exists("ix_stratum_v2_capabilities_observed_at", "stratum_v2_capabilities")
    _drop_index_if_exists("ix_mining_pool_endpoints_pool_id", "mining_pool_endpoints")
    _drop_index_if_exists("ix_mining_pool_endpoints_observed_at", "mining_pool_endpoints")
    _drop_index_if_exists("ix_mining_pools_observed_at", "mining_pools")
    _drop_index_if_exists("ix_mining_pools_display_name", "mining_pools")

    # safe table drops
    for table in [
        "mining_signals",
        "template_control_assessments",
        "mining_censorship_risks",
        "pool_sovereignty_scores",
        "stratum_v2_capabilities",
        "mining_pool_endpoints",
        "mining_pools",
    ]:
        if _has_table(table):
            op.drop_table(table)
