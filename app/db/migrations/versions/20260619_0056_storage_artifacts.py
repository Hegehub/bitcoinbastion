"""create storage artifacts metadata table

Revision ID: 20260619_0056
Revises: 20260608_0055
Create Date: 2026-06-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260619_0056"
down_revision = "20260608_0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("artifact_id", sa.String(length=80), nullable=False),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("artifact_subtype", sa.String(length=80), nullable=True),
        sa.Column("domain", sa.String(length=80), nullable=False),
        sa.Column("object_uri", sa.String(length=2048), nullable=False),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=2048), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("compression", sa.String(length=32), nullable=True),
        sa.Column(
            "encryption_status", sa.String(length=32), nullable=False, server_default="unknown"
        ),
        sa.Column("signature_alg", sa.String(length=64), nullable=True),
        sa.Column("signature_value", sa.Text(), nullable=True),
        sa.Column("signature_key_id", sa.String(length=160), nullable=True),
        sa.Column(
            "retention_policy", sa.String(length=64), nullable=False, server_default="standard"
        ),
        sa.Column("retention_until", sa.DateTime(), nullable=True),
        sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "redaction_status", sa.String(length=32), nullable=False, server_default="not_required"
        ),
        sa.Column("access_policy_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_hash", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.UniqueConstraint("artifact_id", name="uq_storage_artifacts_artifact_id"),
    )
    op.create_index("ix_storage_artifacts_artifact_type", "storage_artifacts", ["artifact_type"])
    op.create_index("ix_storage_artifacts_domain", "storage_artifacts", ["domain"])
    op.create_index("ix_storage_artifacts_sha256_hash", "storage_artifacts", ["sha256_hash"])
    op.create_index(
        "ix_storage_artifacts_bucket_object_key", "storage_artifacts", ["bucket", "object_key"]
    )
    op.create_index("ix_storage_artifacts_created_at", "storage_artifacts", ["created_at"])
    op.create_index(
        "ix_storage_artifacts_retention_policy", "storage_artifacts", ["retention_policy"]
    )
    op.create_index("ix_storage_artifacts_status", "storage_artifacts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_storage_artifacts_status", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_retention_policy", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_created_at", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_bucket_object_key", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_sha256_hash", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_domain", table_name="storage_artifacts")
    op.drop_index("ix_storage_artifacts_artifact_type", table_name="storage_artifacts")
    op.drop_table("storage_artifacts")
