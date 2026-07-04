"""candle lifecycle upgrade

Revision ID: 20260526_0023
Revises: 20260526_0022
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260526_0023"
down_revision = "20260526_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("btc_candles", sa.Column("open", sa.Float(), nullable=True))
    op.add_column("btc_candles", sa.Column("high", sa.Float(), nullable=True))
    op.add_column("btc_candles", sa.Column("low", sa.Float(), nullable=True))
    op.add_column("btc_candles", sa.Column("close", sa.Float(), nullable=True))
    op.add_column("btc_candles", sa.Column("volume", sa.Float(), nullable=True))
    op.add_column(
        "btc_candles",
        sa.Column("provider_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "btc_candles",
        sa.Column("integrity_status", sa.String(32), nullable=False, server_default="valid"),
    )
    op.add_column(
        "btc_candles",
        sa.Column("integrity_notes", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column(
        "btc_candles",
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "btc_candles",
        sa.Column("is_finalized", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "btc_candles", sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "btc_candles",
        sa.Column("rebuild_reason", sa.String(255), nullable=False, server_default=""),
    )
    op.create_index("ix_btc_candles_integrity_status", "btc_candles", ["integrity_status"])
    op.create_index("ix_btc_candles_is_finalized", "btc_candles", ["is_finalized"])


def downgrade() -> None:
    op.drop_index("ix_btc_candles_is_finalized", table_name="btc_candles")
    op.drop_index("ix_btc_candles_integrity_status", table_name="btc_candles")
    for c in [
        "rebuild_reason",
        "revision",
        "is_finalized",
        "is_partial",
        "integrity_notes",
        "integrity_status",
        "provider_snapshot_json",
        "volume",
        "close",
        "low",
        "high",
        "open",
    ]:
        op.drop_column("btc_candles", c)
