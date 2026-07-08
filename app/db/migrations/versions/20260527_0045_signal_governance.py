"""operator signal governance

Revision ID: 20260527_0045
Revises: 20260527_0044
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0045"
down_revision = "20260527_0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intelligence_signal_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("source_entity_type", sa.String(64), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("candle_id", sa.Integer(), sa.ForeignKey("btc_candles.id"), nullable=True),
        sa.Column("impact_id", sa.Integer(), sa.ForeignKey("news_price_impacts.id"), nullable=True),
        sa.Column(
            "attribution_id", sa.Integer(), sa.ForeignKey("candle_attributions.id"), nullable=True
        ),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("btc_relevance_score", sa.Float(), nullable=True),
        sa.Column("market_impact_score", sa.Float(), nullable=True),
        sa.Column("source_confidence", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=True),
        sa.Column("direction_label", sa.String(32), nullable=True),
        sa.Column("dominant_window", sa.String(32), nullable=True),
        sa.Column("evidence_packet_id", sa.String(120), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("policy_decision", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("policy_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "requires_operator_review", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in [
        "signal_type",
        "source_entity_type",
        "source_entity_id",
        "article_id",
        "event_id",
        "candle_id",
        "impact_id",
        "attribution_id",
        "confidence_score",
        "status",
        "policy_decision",
        "requires_operator_review",
        "published_at",
        "created_at",
    ]:
        op.create_index(
            f"ix_intelligence_signal_candidates_{col}", "intelligence_signal_candidates", [col]
        )

    op.create_table(
        "intelligence_operator_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "signal_candidate_id",
            sa.Integer(),
            sa.ForeignKey("intelligence_signal_candidates.id"),
            nullable=False,
        ),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("operator_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("decision_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("false_positive_marker", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence_override", sa.Float(), nullable=True),
        sa.Column("publish_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in [
        "signal_candidate_id",
        "review_status",
        "reviewer_id",
        "false_positive_marker",
        "created_at",
    ]:
        op.create_index(
            f"ix_intelligence_operator_reviews_{col}", "intelligence_operator_reviews", [col]
        )

    op.create_table(
        "intelligence_publishing_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, server_default="default"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_btc_relevance_score", sa.Float(), nullable=False, server_default="0.45"),
        sa.Column("min_impact_confidence", sa.Float(), nullable=False, server_default="0.65"),
        sa.Column("min_source_confidence", sa.Float(), nullable=False, server_default="0.60"),
        sa.Column("min_provider_confidence", sa.Float(), nullable=False, server_default="0.60"),
        sa.Column("allow_auto_publish", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "require_review_for_security_shock",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "require_review_for_regulatory_shock",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "require_review_for_low_confidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "require_review_for_provider_degraded",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "require_review_for_false_signal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("max_signals_per_hour", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_intelligence_publishing_policies_name",
        "intelligence_publishing_policies",
        ["name"],
        unique=True,
    )
    op.create_index(
        "ix_intelligence_publishing_policies_is_active",
        "intelligence_publishing_policies",
        ["is_active"],
    )
    op.bulk_insert(
        sa.table(
            "intelligence_publishing_policies",
            sa.column("name"),
            sa.column("is_active"),
            sa.column("allow_auto_publish"),
        ),
        [{"name": "default", "is_active": True, "allow_auto_publish": False}],
    )

    op.create_table(
        "intelligence_signal_delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "signal_candidate_id",
            sa.Integer(),
            sa.ForeignKey("intelligence_signal_candidates.id"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("delivery_status", sa.String(32), nullable=False),
        sa.Column("target", sa.String(160), nullable=False, server_default=""),
        sa.Column("message_id", sa.String(160), nullable=True),
        sa.Column("error_type", sa.String(120), nullable=True),
        sa.Column("error_message_sanitized", sa.String(500), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["signal_candidate_id", "channel", "delivery_status", "created_at"]:
        op.create_index(
            f"ix_intelligence_signal_delivery_logs_{col}",
            "intelligence_signal_delivery_logs",
            [col],
        )


def downgrade() -> None:
    for col in ["created_at", "delivery_status", "channel", "signal_candidate_id"]:
        op.drop_index(
            f"ix_intelligence_signal_delivery_logs_{col}",
            table_name="intelligence_signal_delivery_logs",
        )
    op.drop_table("intelligence_signal_delivery_logs")
    op.drop_index(
        "ix_intelligence_publishing_policies_is_active",
        table_name="intelligence_publishing_policies",
    )
    op.drop_index(
        "ix_intelligence_publishing_policies_name", table_name="intelligence_publishing_policies"
    )
    op.drop_table("intelligence_publishing_policies")
    for col in [
        "created_at",
        "false_positive_marker",
        "reviewer_id",
        "review_status",
        "signal_candidate_id",
    ]:
        op.drop_index(
            f"ix_intelligence_operator_reviews_{col}", table_name="intelligence_operator_reviews"
        )
    op.drop_table("intelligence_operator_reviews")
    for col in [
        "created_at",
        "published_at",
        "requires_operator_review",
        "policy_decision",
        "status",
        "confidence_score",
        "attribution_id",
        "impact_id",
        "candle_id",
        "event_id",
        "article_id",
        "source_entity_id",
        "source_entity_type",
        "signal_type",
    ]:
        op.drop_index(
            f"ix_intelligence_signal_candidates_{col}", table_name="intelligence_signal_candidates"
        )
    op.drop_table("intelligence_signal_candidates")
