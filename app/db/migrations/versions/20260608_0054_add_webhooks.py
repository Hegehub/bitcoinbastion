"""add webhooks

Revision ID: 20260608_0054
Revises: 20260607_0053
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "20260608_0054"
down_revision = "20260607_0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_delivery_at", sa.DateTime(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("secret_ref", sa.String(length=160), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_webhook_endpoints_enabled", "webhook_endpoints", ["enabled"])
    op.create_index("ix_webhook_endpoints_status", "webhook_endpoints", ["status"])
    op.create_index("ix_webhook_endpoints_created_at", "webhook_endpoints", ["created_at"])

    op.create_table(
        "webhook_event_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "webhook_endpoint_id",
            sa.Integer(),
            sa.ForeignKey("webhook_endpoints.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "webhook_endpoint_id", "event_type", name="uq_webhook_subscription_endpoint_event"
        ),
    )
    op.create_index(
        "ix_webhook_subscriptions_endpoint", "webhook_event_subscriptions", ["webhook_endpoint_id"]
    )
    op.create_index(
        "ix_webhook_subscriptions_event_type", "webhook_event_subscriptions", ["event_type"]
    )
    op.create_index("ix_webhook_subscriptions_enabled", "webhook_event_subscriptions", ["enabled"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "webhook_endpoint_id",
            sa.Integer(),
            sa.ForeignKey("webhook_endpoints.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("event_outbox_id", sa.Integer(), sa.ForeignKey("event_outbox.id"), nullable=True),
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("request_headers_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("request_body_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body_preview", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_webhook_deliveries_endpoint", "webhook_deliveries", ["webhook_endpoint_id"])
    op.create_index("ix_webhook_deliveries_event_type", "webhook_deliveries", ["event_type"])
    op.create_index(
        "ix_webhook_deliveries_delivery_id", "webhook_deliveries", ["delivery_id"], unique=True
    )
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"])
    op.create_index("ix_webhook_deliveries_created_at", "webhook_deliveries", ["created_at"])
    op.create_index(
        "ix_webhook_deliveries_next_attempt_at", "webhook_deliveries", ["next_attempt_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_next_attempt_at", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_created_at", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_status", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_delivery_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_event_type", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_endpoint", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhook_subscriptions_enabled", table_name="webhook_event_subscriptions")
    op.drop_index("ix_webhook_subscriptions_event_type", table_name="webhook_event_subscriptions")
    op.drop_index("ix_webhook_subscriptions_endpoint", table_name="webhook_event_subscriptions")
    op.drop_table("webhook_event_subscriptions")
    op.drop_index("ix_webhook_endpoints_created_at", table_name="webhook_endpoints")
    op.drop_index("ix_webhook_endpoints_status", table_name="webhook_endpoints")
    op.drop_index("ix_webhook_endpoints_enabled", table_name="webhook_endpoints")
    op.drop_table("webhook_endpoints")
