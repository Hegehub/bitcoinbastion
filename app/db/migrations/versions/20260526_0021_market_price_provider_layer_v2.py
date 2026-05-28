"""market price provider layer v2

Revision ID: 20260526_0021
Revises: 20260526_0020
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0021"
down_revision = "20260526_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_provider_health",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_name", sa.String(32), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("backoff_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_market_provider_health_provider_name", "market_provider_health", ["provider_name"], unique=True)
    op.create_index("ix_market_provider_health_updated_at", "market_provider_health", ["updated_at"])

    op.add_column("btc_price_points", sa.Column("provider_name", sa.String(32), nullable=True))
    op.add_column("btc_price_points", sa.Column("symbol", sa.String(16), nullable=False, server_default="BTC"))
    op.add_column("btc_price_points", sa.Column("provider_latency_ms", sa.Integer(), nullable=True))
    op.add_column("btc_price_points", sa.Column("aggregation_round_id", sa.String(64), nullable=False, server_default=""))
    op.add_column("btc_price_points", sa.Column("is_median_selected", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_btc_price_points_provider_name", "btc_price_points", ["provider_name"])


def downgrade() -> None:
    op.drop_index("ix_btc_price_points_provider_name", table_name="btc_price_points")
    for col in ["is_median_selected", "aggregation_round_id", "provider_latency_ms", "symbol", "provider_name"]:
        op.drop_column("btc_price_points", col)
    op.drop_index("ix_market_provider_health_updated_at", table_name="market_provider_health")
    op.drop_index("ix_market_provider_health_provider_name", table_name="market_provider_health")
    op.drop_table("market_provider_health")
