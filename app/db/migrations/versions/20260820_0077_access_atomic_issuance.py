"""add device-bound Access issuance challenges and grants

Revision ID: 20260820_0077
Revises: 20260820_0076
"""

from alembic import op
import sqlalchemy as sa

revision = "20260820_0077"
down_revision = "20260820_0076"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_issuance_challenges",
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("checkout_id", sa.String(96), sa.ForeignKey("access_checkout_sessions.id"), nullable=False),
        sa.Column("device_public_key", sa.Text(), nullable=False),
        sa.Column("device_key_fingerprint", sa.String(128), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("protocol_version", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_access_issuance_challenges_checkout_id", "access_issuance_challenges", ["checkout_id"])
    op.create_index("ix_access_issuance_challenges_device_key_fingerprint", "access_issuance_challenges", ["device_key_fingerprint"])
    op.create_index("ix_access_issuance_challenges_expires_at", "access_issuance_challenges", ["expires_at"])
    op.create_index("ix_access_issuance_challenges_status", "access_issuance_challenges", ["status"])
    op.create_table(
        "access_issued_grants",
        sa.Column("id", sa.String(96), primary_key=True),
        sa.Column("checkout_id", sa.String(96), sa.ForeignKey("access_checkout_sessions.id"), nullable=False, unique=True),
        sa.Column("offer_revision_id", sa.String(128), nullable=False),
        sa.Column("certificate_fingerprint", sa.String(128), nullable=False, unique=True),
        sa.Column("device_key_fingerprint", sa.String(128), nullable=False),
        sa.Column("capability", sa.String(80), nullable=False),
        sa.Column("scopes_json", sa.JSON(), nullable=False),
        sa.Column("terms_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_access_issued_grants_device_key_fingerprint", "access_issued_grants", ["device_key_fingerprint"])


def downgrade() -> None:
    op.drop_table("access_issued_grants")
    op.drop_table("access_issuance_challenges")
