"""historical similarity engine and narrative memory finalization

Revision ID: 20260527_0048
Revises: 20260527_0047
Create Date: 2026-05-27 00:48:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260527_0048"
down_revision = "20260527_0047"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.add_column(
        "market_patterns",
        sa.Column("display_name", sa.String(length=160), nullable=False, server_default=""),
    )
    op.add_column(
        "market_patterns",
        sa.Column(
            "typical_sentiment", sa.String(length=32), nullable=False, server_default="UNKNOWN"
        ),
    )
    op.add_column(
        "market_patterns",
        sa.Column(
            "typical_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"
        ),
    )
    op.add_column(
        "market_patterns",
        sa.Column("default_time_window", sa.String(length=32), nullable=False, server_default="1h"),
    )
    op.execute("UPDATE market_patterns SET display_name = name WHERE display_name = ''")
    op.execute(
        "UPDATE market_patterns SET typical_sentiment = expected_sentiment WHERE typical_sentiment = 'UNKNOWN'"
    )
    op.execute(
        "UPDATE market_patterns SET typical_direction = expected_direction WHERE typical_direction = 'UNKNOWN'"
    )
    op.execute(
        "UPDATE market_patterns SET default_time_window = typical_impact_window WHERE default_time_window = '1h'"
    )

    with op.batch_alter_table("pattern_occurrences") as batch_op:
        batch_op.add_column(sa.Column("signal_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "classification_reason", sa.String(length=1000), nullable=False, server_default=""
            )
        )
        batch_op.create_index("ix_pattern_occurrences_signal_id", ["signal_id"])
        batch_op.create_foreign_key(
            "fk_pattern_occurrences_signal_id_intelligence_signal_candidates",
            "intelligence_signal_candidates",
            ["signal_id"],
            ["id"],
        )

    with op.batch_alter_table("historical_similarity_matches") as batch_op:
        batch_op.add_column(sa.Column("reference_occurrence_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("candidate_occurrence_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("time_structure_score", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("sentiment_match", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("direction_match", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.create_index(
            "ix_historical_similarity_matches_reference_occurrence_id", ["reference_occurrence_id"]
        )
        batch_op.create_index(
            "ix_historical_similarity_matches_candidate_occurrence_id", ["candidate_occurrence_id"]
        )
        batch_op.create_foreign_key(
            "fk_hsm_reference_occurrence_id_pattern_occurrences",
            "pattern_occurrences",
            ["reference_occurrence_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_hsm_candidate_occurrence_id_pattern_occurrences",
            "pattern_occurrences",
            ["candidate_occurrence_id"],
            ["id"],
        )

    op.create_table(
        "historical_reaction_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column("samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("median_move_15m", sa.Float(), nullable=True),
        sa.Column("median_move_1h", sa.Float(), nullable=True),
        sa.Column("median_move_4h", sa.Float(), nullable=True),
        sa.Column("median_move_24h", sa.Float(), nullable=True),
        sa.Column("positive_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("negative_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("neutral_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_historical_reaction_statistics_pattern_id",
        "historical_reaction_statistics",
        ["pattern_id"],
        unique=True,
    )

    op.create_table(
        "pattern_embeddings_placeholder",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column(
            "embedding_provider", sa.String(length=64), nullable=False, server_default="none"
        ),
        sa.Column(
            "embedding_version",
            sa.String(length=64),
            nullable=False,
            server_default="deterministic_placeholder",
        ),
        sa.Column("vector_json", json_type, nullable=False, server_default="[]"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_pattern_embeddings_placeholder_pattern_id",
        "pattern_embeddings_placeholder",
        ["pattern_id"],
    )

    op.create_table(
        "narrative_memory_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("narrative", sa.String(length=96), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weighted_impact", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_quality", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_reaction", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_decay", sa.Float(), nullable=False, server_default="1"),
        sa.Column("heat_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("strength_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("decay_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_narrative_memory_snapshots_narrative", "narrative_memory_snapshots", ["narrative"]
    )
    op.create_index(
        "ix_narrative_memory_snapshots_snapshot_time",
        "narrative_memory_snapshots",
        ["snapshot_time"],
    )
    op.create_index(
        "ix_narrative_memory_snapshots_heat_score", "narrative_memory_snapshots", ["heat_score"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_narrative_memory_snapshots_heat_score", table_name="narrative_memory_snapshots"
    )
    op.drop_index(
        "ix_narrative_memory_snapshots_snapshot_time", table_name="narrative_memory_snapshots"
    )
    op.drop_index(
        "ix_narrative_memory_snapshots_narrative", table_name="narrative_memory_snapshots"
    )
    op.drop_table("narrative_memory_snapshots")
    op.drop_index(
        "ix_pattern_embeddings_placeholder_pattern_id", table_name="pattern_embeddings_placeholder"
    )
    op.drop_table("pattern_embeddings_placeholder")
    op.drop_index(
        "ix_historical_reaction_statistics_pattern_id", table_name="historical_reaction_statistics"
    )
    op.drop_table("historical_reaction_statistics")
    with op.batch_alter_table("historical_similarity_matches") as batch_op:
        batch_op.drop_index("ix_historical_similarity_matches_candidate_occurrence_id")
        batch_op.drop_index("ix_historical_similarity_matches_reference_occurrence_id")
        batch_op.drop_column("overall_confidence")
        batch_op.drop_column("provider_confidence")
        batch_op.drop_column("direction_match")
        batch_op.drop_column("sentiment_match")
        batch_op.drop_column("time_structure_score")
        batch_op.drop_column("candidate_occurrence_id")
        batch_op.drop_column("reference_occurrence_id")
    with op.batch_alter_table("pattern_occurrences") as batch_op:
        batch_op.drop_constraint(
            "fk_pattern_occurrences_signal_id_intelligence_signal_candidates", type_="foreignkey"
        )
        batch_op.drop_index("ix_pattern_occurrences_signal_id")
        batch_op.drop_column("classification_reason")
        batch_op.drop_column("signal_id")
    op.drop_column("market_patterns", "default_time_window")
    op.drop_column("market_patterns", "typical_direction")
    op.drop_column("market_patterns", "typical_sentiment")
    op.drop_column("market_patterns", "display_name")
