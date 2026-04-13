"""expand domain models

Revision ID: 20260413_0002
Revises: 20260413_0001
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("news_sources", sa.Column("language", sa.String(length=8), nullable=False, server_default="en"))
    op.add_column("news_sources", sa.Column("category", sa.String(length=80), nullable=False, server_default="general"))
    op.add_column("news_sources", sa.Column("last_fetched_at", sa.DateTime(), nullable=True))

    op.add_column("news_articles", sa.Column("canonical_hash", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("news_articles", sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("news_articles", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column("news_articles", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    op.add_column("onchain_events", sa.Column("fee_sats", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("onchain_events", sa.Column("entity_id", sa.Integer(), nullable=True))
    op.add_column("onchain_events", sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("onchain_events", sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("onchain_events", sa.Column("tags_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("onchain_events", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column("onchain_events", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    op.add_column("signals", sa.Column("version", sa.String(length=40), nullable=False, server_default="v1"))
    op.add_column("signals", sa.Column("status", sa.String(length=30), nullable=False, server_default="new"))
    op.add_column("signals", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    op.add_column("watched_entities", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("watched_entities", sa.Column("entity_id", sa.Integer(), nullable=True))
    op.add_column("watched_entities", sa.Column("address", sa.String(length=128), nullable=False, server_default=""))
    op.add_column("watched_entities", sa.Column("watch_type", sa.String(length=40), nullable=False, server_default="entity"))
    op.add_column("watched_entities", sa.Column("threshold_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("watched_entities", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    op.create_table(
        "signal_source_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "wallet_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("descriptor_or_reference", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("wallet_type", sa.String(length=50), nullable=False, server_default="single-sig"),
        sa.Column("watch_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "wallet_health_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wallet_profile_id", sa.Integer(), sa.ForeignKey("wallet_profiles.id"), nullable=False),
        sa.Column("health_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("utxo_fragmentation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("privacy_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fee_exposure_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("findings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("recommendations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "treasury_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_reference", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("amount_sats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("destination_reference", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=30), nullable=False, server_default="normal"),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("approved_by_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("required_approvals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("policy_snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "psbt_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("treasury_request_id", sa.Integer(), sa.ForeignKey("treasury_requests.id"), nullable=False),
        sa.Column("psbt_reference", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("signer_requirements_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=True),
        sa.Column("digest_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("channel_type", sa.String(length=40), nullable=False, server_default="telegram"),
        sa.Column("destination", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("provider_message_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("delivery_status", sa.String(length=40), nullable=False, server_default="sent"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload_snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("delivery_logs")
    op.drop_table("psbt_workflows")
    op.drop_table("treasury_requests")
    op.drop_table("wallet_health_reports")
    op.drop_table("wallet_profiles")
    op.drop_table("signal_source_links")

    op.drop_column("watched_entities", "is_active")
    op.drop_column("watched_entities", "threshold_json")
    op.drop_column("watched_entities", "watch_type")
    op.drop_column("watched_entities", "address")
    op.drop_column("watched_entities", "entity_id")
    op.drop_column("watched_entities", "user_id")

    op.drop_column("signals", "updated_at")
    op.drop_column("signals", "status")
    op.drop_column("signals", "version")

    op.drop_column("onchain_events", "updated_at")
    op.drop_column("onchain_events", "created_at")
    op.drop_column("onchain_events", "tags_json")
    op.drop_column("onchain_events", "confidence_score")
    op.drop_column("onchain_events", "explainability_json")
    op.drop_column("onchain_events", "entity_id")
    op.drop_column("onchain_events", "fee_sats")

    op.drop_column("news_articles", "updated_at")
    op.drop_column("news_articles", "created_at")
    op.drop_column("news_articles", "explainability_json")
    op.drop_column("news_articles", "canonical_hash")

    op.drop_column("news_sources", "last_fetched_at")
    op.drop_column("news_sources", "category")
    op.drop_column("news_sources", "language")
