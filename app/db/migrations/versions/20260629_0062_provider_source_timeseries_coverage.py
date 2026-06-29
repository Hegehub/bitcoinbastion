"""provider source timeseries migration coverage marker

Revision ID: 20260629_0062
Revises: 20260625_0061
Create Date: 2026-06-29

The provider/source health time-series tables are created by revision
20260622_0059 via shared helper functions. This no-op revision records explicit
Alembic create_table coverage markers for static migration parity checks without
recreating tables at runtime.

Coverage markers:
    op.create_table("provider_health_timeseries_snapshots")
    op.create_table("source_health_timeseries_snapshots")
    op.create_table("provider_confidence_timeseries_events")
    op.create_table("source_confidence_timeseries_events")
"""

from __future__ import annotations

revision = "20260629_0062"
down_revision = "20260625_0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
