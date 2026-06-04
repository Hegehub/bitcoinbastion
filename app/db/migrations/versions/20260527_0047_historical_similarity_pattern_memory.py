"""historical similarity pattern memory production finalization

Revision ID: 20260527_0047
Revises: 20260527_0046
Create Date: 2026-05-27 00:47:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260527_0047"
down_revision = "20260527_0046"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.add_column("market_patterns", sa.Column("pattern_code", sa.String(length=96), nullable=False, server_default=""))
    op.add_column("market_patterns", sa.Column("default_sentiment", sa.String(length=32), nullable=False, server_default="UNKNOWN"))
    op.add_column("market_patterns", sa.Column("default_impact_window", sa.String(length=32), nullable=False, server_default="1h"))
    op.add_column("market_patterns", sa.Column("risk_profile", sa.String(length=64), nullable=False, server_default="standard"))
    op.execute("UPDATE market_patterns SET pattern_code = slug WHERE pattern_code = ''")
    op.execute("UPDATE market_patterns SET default_sentiment = expected_sentiment WHERE default_sentiment = 'UNKNOWN'")
    op.execute("UPDATE market_patterns SET default_impact_window = typical_impact_window")
    op.create_index("ix_market_patterns_pattern_code", "market_patterns", ["pattern_code"])

    op.create_table(
        "pattern_occurrences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id", name="fk_pattern_occurrences_pattern_id_market_patterns"), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id", name="fk_pattern_occurrences_event_id_news_events"), nullable=True),
        sa.Column("impact_id", sa.Integer(), sa.ForeignKey("news_price_impacts.id"), nullable=True),
        sa.Column("attribution_id", sa.Integer(), sa.ForeignKey("candle_attributions.id"), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["pattern_id", "article_id", "event_id", "impact_id", "attribution_id", "occurred_at", "confidence_score"]:
        op.create_index(f"ix_pattern_occurrences_{col}", "pattern_occurrences", [col])

    with op.batch_alter_table("historical_similarity_results") as batch_op:
        batch_op.add_column(sa.Column("source_event_id", sa.Integer(), sa.ForeignKey("news_events.id", name="fk_hsr_source_event_id_news_events"), nullable=True))
        batch_op.add_column(sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id", name="fk_hsr_pattern_id_market_patterns"), nullable=True))
        batch_op.add_column(sa.Column("reaction_similarity_score", sa.Float(), nullable=False, server_default="0"))
        batch_op.create_index("ix_historical_similarity_results_source_event_id", ["source_event_id"])
        batch_op.create_index("ix_historical_similarity_results_pattern_id", ["pattern_id"])

    op.add_column("pattern_statistics", sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("pattern_statistics", sa.Column("avg_move_15m", sa.Float(), nullable=True))
    op.add_column("pattern_statistics", sa.Column("avg_move_1h", sa.Float(), nullable=True))
    op.add_column("pattern_statistics", sa.Column("avg_move_4h", sa.Float(), nullable=True))
    op.add_column("pattern_statistics", sa.Column("avg_move_24h", sa.Float(), nullable=True))
    op.add_column("pattern_statistics", sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"))
    op.add_column("pattern_statistics", sa.Column("last_updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.execute("UPDATE pattern_statistics SET occurrence_count = historical_occurrences")
    op.execute("UPDATE pattern_statistics SET success_rate = positive_rate")

    op.create_table(
        "pattern_reaction_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column("occurrence_id", sa.Integer(), sa.ForeignKey("pattern_occurrences.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("reaction_window", sa.String(length=32), nullable=False, server_default="4h"),
        sa.Column("move_pct", sa.Float(), nullable=True),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reaction_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["pattern_id", "occurrence_id", "event_id", "reaction_window", "direction"]:
        op.create_index(f"ix_pattern_reaction_snapshots_{col}", "pattern_reaction_snapshots", [col])

    op.add_column("market_narratives", sa.Column("first_seen", sa.DateTime(), nullable=True))
    op.add_column("market_narratives", sa.Column("last_seen", sa.DateTime(), nullable=True))
    op.add_column("market_narratives", sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("market_narratives", sa.Column("avg_confidence", sa.Float(), nullable=False, server_default="0"))
    op.add_column("market_narratives", sa.Column("related_patterns", json_type, nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("market_narratives", "related_patterns")
    op.drop_column("market_narratives", "avg_confidence")
    op.drop_column("market_narratives", "event_count")
    op.drop_column("market_narratives", "last_seen")
    op.drop_column("market_narratives", "first_seen")
    for col in ["direction", "reaction_window", "event_id", "occurrence_id", "pattern_id"]:
        op.drop_index(f"ix_pattern_reaction_snapshots_{col}", table_name="pattern_reaction_snapshots")
    op.drop_table("pattern_reaction_snapshots")
    op.drop_column("pattern_statistics", "last_updated_at")
    op.drop_column("pattern_statistics", "success_rate")
    op.drop_column("pattern_statistics", "avg_move_24h")
    op.drop_column("pattern_statistics", "avg_move_4h")
    op.drop_column("pattern_statistics", "avg_move_1h")
    op.drop_column("pattern_statistics", "avg_move_15m")
    op.drop_column("pattern_statistics", "occurrence_count")
    with op.batch_alter_table("historical_similarity_results") as batch_op:
        batch_op.drop_index("ix_historical_similarity_results_pattern_id")
        batch_op.drop_index("ix_historical_similarity_results_source_event_id")
        batch_op.drop_column("reaction_similarity_score")
        batch_op.drop_column("pattern_id")
        batch_op.drop_column("source_event_id")
    for col in ["confidence_score", "occurred_at", "attribution_id", "impact_id", "event_id", "article_id", "pattern_id"]:
        op.drop_index(f"ix_pattern_occurrences_{col}", table_name="pattern_occurrences")
    op.drop_table("pattern_occurrences")
    op.drop_index("ix_market_patterns_pattern_code", table_name="market_patterns")
    op.drop_column("market_patterns", "risk_profile")
    op.drop_column("market_patterns", "default_impact_window")
    op.drop_column("market_patterns", "default_sentiment")
    op.drop_column("market_patterns", "pattern_code")
