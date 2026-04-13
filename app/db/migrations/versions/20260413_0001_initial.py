"""initial schema

Revision ID: 20260413_0001
Revises: 
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("preferences_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("features_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("limits_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("billing_provider", sa.String(length=40), nullable=False, server_default="manual"),
        sa.Column("external_subscription_id", sa.String(length=120), nullable=False, server_default=""),
    )

    op.create_table(
        "news_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False, server_default="rss"),
        sa.Column("base_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("rss_url", sa.String(length=255), nullable=False),
        sa.Column("credibility_weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("news_sources.id"), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("content_raw", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_clean", sa.Text(), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("duplicate_of_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("btc_relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("urgency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("credibility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"], unique=False)

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("explainability_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "onchain_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("txid", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("address", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("value_sats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("block_height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False, server_default="mock"),
        sa.Column("raw_payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("significance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tags", sa.String(length=255), nullable=False, server_default=""),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "entity_addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("address", sa.String(length=128), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=False, server_default="bitcoin"),
        sa.Column("label", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_refs_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "watched_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("addresses_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "telegram_delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("chat_id", sa.String(length=120), nullable=False),
        sa.Column("message_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("delivery_type", sa.String(length=40), nullable=False, server_default="signal"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("after_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "telegram_delivery_logs",
        "watched_entities",
        "entity_addresses",
        "entities",
        "onchain_events",
        "signals",
        "news_articles",
        "news_sources",
        "user_subscriptions",
        "subscription_plans",
        "users",
    ]:
        op.drop_table(table)
