"""market data provider layer

Revision ID: 20260526_0020
Revises: 20260526_0019
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0020"
down_revision = "20260526_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "btc_price_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("pair", sa.String(16), nullable=False, server_default="BTCUSD"),
        sa.Column("price_usd", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("raw_payload_hash", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_btc_price_points_provider", "btc_price_points", ["provider"])
    op.create_index("ix_btc_price_points_observed_at", "btc_price_points", ["observed_at"])
    op.create_index("ix_btc_price_points_pair", "btc_price_points", ["pair"])

    op.create_table(
        "provider_health_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("backoff_until", sa.DateTime(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_provider_health_records_provider", "provider_health_records", ["provider"], unique=True
    )
    op.create_index(
        "ix_provider_health_records_is_degraded", "provider_health_records", ["is_degraded"]
    )


def downgrade() -> None:
    op.drop_index("ix_provider_health_records_is_degraded", table_name="provider_health_records")
    op.drop_index("ix_provider_health_records_provider", table_name="provider_health_records")
    op.drop_table("provider_health_records")
    op.drop_index("ix_btc_price_points_pair", table_name="btc_price_points")
    op.drop_index("ix_btc_price_points_observed_at", table_name="btc_price_points")
    op.drop_index("ix_btc_price_points_provider", table_name="btc_price_points")
    op.drop_table("btc_price_points")
