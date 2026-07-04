"""intelligence timeline foundation

Revision ID: 20260527_0025
Revises: 20260527_0024
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0025"
down_revision = "20260527_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intelligence_timeline_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("importance", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("visibility", sa.String(16), nullable=False, server_default="INTERNAL"),
        sa.Column("source_kind", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column(
            "related_article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True
        ),
        sa.Column("related_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("related_signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=True),
        sa.Column(
            "related_candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=True
        ),
        sa.Column(
            "related_provider_id",
            sa.Integer(),
            sa.ForeignKey("market_provider_health.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("summary", sa.String(1000), nullable=False, server_default=""),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("btc_price_reference", sa.Float(), nullable=True),
        sa.Column("btc_price_delta_pct", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=True),
        sa.Column("timeline_rank", sa.Float(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("evidence_refs_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("limitations_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_replayed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_intel_timeline_event_time", "intelligence_timeline_events", ["event_time"])
    op.create_index("ix_intel_timeline_event_type", "intelligence_timeline_events", ["event_type"])
    op.create_index(
        "ix_intel_timeline_event_type_time",
        "intelligence_timeline_events",
        ["event_type", "event_time"],
    )


def downgrade() -> None:
    op.drop_index("ix_intel_timeline_event_type_time", table_name="intelligence_timeline_events")
    op.drop_index("ix_intel_timeline_event_type", table_name="intelligence_timeline_events")
    op.drop_index("ix_intel_timeline_event_time", table_name="intelligence_timeline_events")
    op.drop_table("intelligence_timeline_events")
