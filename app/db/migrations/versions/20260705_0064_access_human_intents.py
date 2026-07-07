"""access human intents

Revision ID: 20260705_0064
Revises: 20260701_0063
Create Date: 2026-07-05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260705_0064"
down_revision = "20260701_0063"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _has_table("access_human_intents"):
        op.create_table(
            "access_human_intents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("intent_hash", sa.String(length=128), nullable=False),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("certificate_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("device_key_fingerprint", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="created"),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("canonical_manifest_json", sa.JSON(), nullable=False),
            sa.Column("signature_hash", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    indexes = {idx["name"] for idx in inspect(op.get_bind()).get_indexes("access_human_intents")}
    for name, columns, unique in (
        ("ix_access_human_intents_intent_hash", ["intent_hash"], True),
        ("ix_access_human_intents_action", ["action"], False),
        ("ix_access_human_intents_certificate_fingerprint", ["certificate_fingerprint"], False),
        ("ix_access_human_intents_device_key_fingerprint", ["device_key_fingerprint"], False),
        ("ix_access_human_intents_status", ["status"], False),
        ("ix_access_human_intents_expires_at", ["expires_at"], False),
        ("ix_access_human_intents_cert_action", ["certificate_fingerprint", "action"], False),
        ("ix_access_human_intents_status_expires", ["status", "expires_at"], False),
    ):
        if name not in indexes:
            op.create_index(name, "access_human_intents", columns, unique=unique)


def downgrade() -> None:
    if _has_table("access_human_intents"):
        op.drop_table("access_human_intents")
