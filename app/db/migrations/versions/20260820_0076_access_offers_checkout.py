"""add authoritative Access checkout sessions

Revision ID: 20260820_0076
Revises: 20260815_0075
"""

from alembic import op
import sqlalchemy as sa

revision = "20260820_0076"
down_revision = "20260815_0075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_checkout_sessions",
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("idempotency_key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("offer_id", sa.String(64), nullable=False),
        sa.Column("offer_revision_id", sa.String(128), nullable=False),
        sa.Column("plan_code", sa.String(40), nullable=False),
        sa.Column("capability", sa.String(80), nullable=False),
        sa.Column("scopes_json", sa.JSON(), nullable=False),
        sa.Column("amount_sats", sa.Integer(), nullable=False),
        sa.Column("price_unit", sa.String(16), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("terms_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("eligibility_reason", sa.String(48), nullable=False),
        sa.Column("payment_intent_id", sa.Integer(), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_access_checkout_offer", "access_checkout_sessions", ["offer_id"])
    op.create_index("ix_access_checkout_revision", "access_checkout_sessions", ["offer_revision_id"])
    op.create_index("ix_access_checkout_status", "access_checkout_sessions", ["status"])
    with op.batch_alter_table("access_payment_intents") as batch:
        batch.add_column(sa.Column("checkout_id", sa.String(96), nullable=True))
        batch.create_foreign_key("fk_access_payment_checkout", "access_checkout_sessions", ["checkout_id"], ["id"])
        batch.create_unique_constraint("uq_access_payment_checkout", ["checkout_id"])


def downgrade() -> None:
    with op.batch_alter_table("access_payment_intents") as batch:
        batch.drop_constraint("uq_access_payment_checkout", type_="unique")
        batch.drop_constraint("fk_access_payment_checkout", type_="foreignkey")
        batch.drop_column("checkout_id")
    op.drop_table("access_checkout_sessions")
