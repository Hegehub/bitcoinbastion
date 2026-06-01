"""narrative heatmap task 34 production fields

Revision ID: 20260527_0043
Revises: 20260527_0042
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0043"
down_revision = "20260527_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("narrative_observations", sa.Column("narrative_id", sa.Integer(), nullable=True))
    op.add_column("narrative_observations", sa.Column("observation_time", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column("narrative_observations", sa.Column("strength_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("narrative_observations", sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"))
    op.create_index("ix_narrative_observations_narrative_id", "narrative_observations", ["narrative_id"])
    op.create_index("ix_narrative_observations_observation_time", "narrative_observations", ["observation_time"])

    op.add_column("narrative_snapshots", sa.Column("velocity_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("narrative_snapshots", sa.Column("dominance_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("narrative_snapshots", sa.Column("supporting_events_count", sa.Integer(), nullable=False, server_default="0"))

    conn = op.get_bind()
    conn.execute(sa.text("update narrative_observations set observation_time = observed_at where observed_at is not null"))
    conn.execute(
        sa.text(
            """
            update narrative_observations
            set narrative_id = (
                select market_narratives.id
                from market_narratives
                where market_narratives.narrative_type = narrative_observations.narrative_type
                limit 1
            )
            where narrative_id is null
            """
        )
    )
    conn.execute(sa.text("update narrative_observations set strength_score = observation_score where strength_score = 0"))
    conn.execute(sa.text("update narrative_observations set relevance_score = observation_score where relevance_score = 0"))
    conn.execute(sa.text("update narrative_snapshots set velocity_score = case when growth_score > 0 then growth_score else 0 end"))
    conn.execute(sa.text("update narrative_snapshots set supporting_events_count = event_count"))


def downgrade() -> None:
    op.drop_column("narrative_snapshots", "supporting_events_count")
    op.drop_column("narrative_snapshots", "dominance_score")
    op.drop_column("narrative_snapshots", "velocity_score")
    op.drop_index("ix_narrative_observations_observation_time", table_name="narrative_observations")
    op.drop_index("ix_narrative_observations_narrative_id", table_name="narrative_observations")
    op.drop_column("narrative_observations", "relevance_score")
    op.drop_column("narrative_observations", "strength_score")
    op.drop_column("narrative_observations", "observation_time")
    op.drop_column("narrative_observations", "narrative_id")
