"""Add production pattern catalog fields.

Revision ID: 20260527_0038
Revises: 20260527_0037
Create Date: 2026-05-27 00:38:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260527_0038"
down_revision = "20260527_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "market_pattern_library",
        sa.Column(
            "default_sentiment", sa.String(length=32), nullable=False, server_default="UNKNOWN"
        ),
    )
    op.add_column(
        "market_pattern_library",
        sa.Column(
            "expected_reaction_window",
            sa.String(length=32),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.add_column(
        "market_pattern_library",
        sa.Column(
            "expected_volatility", sa.String(length=32), nullable=False, server_default="normal"
        ),
    )
    op.add_column(
        "market_pattern_library",
        sa.Column("confidence_modifier", sa.Float(), nullable=False, server_default="1.0"),
    )

    op.execute("UPDATE market_pattern_library SET default_sentiment = expected_sentiment")
    op.execute(
        "UPDATE market_pattern_library SET expected_reaction_window = '15m' WHERE pattern_code LIKE '%ETF%' OR pattern_code LIKE '%HACK%' OR pattern_code LIKE '%LIQUIDATION%' OR pattern_code LIKE '%SECURITY%'"
    )
    op.execute(
        "UPDATE market_pattern_library SET expected_reaction_window = '1h' WHERE expected_reaction_window = 'unknown'"
    )
    op.execute(
        "UPDATE market_pattern_library SET expected_volatility = 'elevated' WHERE pattern_code LIKE '%SHOCK%' OR pattern_code LIKE '%HACK%' OR pattern_code LIKE '%EXPLOIT%' OR pattern_code LIKE '%LIQUIDATION%' OR pattern_code LIKE '%VOLATILITY%'"
    )
    op.execute(
        "UPDATE market_pattern_library SET confidence_modifier = 1.05 WHERE pattern_code LIKE '%ETF%' OR pattern_code LIKE '%HACK%' OR pattern_code LIKE '%EXPLOIT%' OR pattern_code LIKE '%LIQUIDATION%'"
    )


def downgrade() -> None:
    op.drop_column("market_pattern_library", "confidence_modifier")
    op.drop_column("market_pattern_library", "expected_volatility")
    op.drop_column("market_pattern_library", "expected_reaction_window")
    op.drop_column("market_pattern_library", "default_sentiment")
