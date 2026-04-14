"""add policy runtime tables

Revision ID: 20260414_0004
Revises: 20260413_0003
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0004"
down_revision = "20260413_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treasury_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("min_wallet_health_score", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_single_tx_sats", sa.Integer(), nullable=False, server_default="10000000"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_treasury_policies_name", "treasury_policies", ["name"], unique=True)

    op.create_table(
        "policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("treasury_policies.id"), nullable=False),
        sa.Column("rule_key", sa.String(length=120), nullable=False),
        sa.Column("rule_value", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="warning"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_policy_rules_policy_id", "policy_rules", ["policy_id"], unique=False)
    op.create_index("ix_policy_rules_rule_key", "policy_rules", ["rule_key"], unique=False)

    op.create_table(
        "policy_execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_name", sa.String(length=120), nullable=False),
        sa.Column("wallet_health_score", sa.Integer(), nullable=False),
        sa.Column("transaction_amount_sats", sa.Integer(), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("violations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("next_actions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_policy_execution_logs_policy_name",
        "policy_execution_logs",
        ["policy_name"],
        unique=False,
    )
    op.create_index(
        "ix_policy_execution_logs_executed_at",
        "policy_execution_logs",
        ["executed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_policy_execution_logs_executed_at", table_name="policy_execution_logs")
    op.drop_index("ix_policy_execution_logs_policy_name", table_name="policy_execution_logs")
    op.drop_table("policy_execution_logs")

    op.drop_index("ix_policy_rules_rule_key", table_name="policy_rules")
    op.drop_index("ix_policy_rules_policy_id", table_name="policy_rules")
    op.drop_table("policy_rules")

    op.drop_index("ix_treasury_policies_name", table_name="treasury_policies")
    op.drop_table("treasury_policies")
