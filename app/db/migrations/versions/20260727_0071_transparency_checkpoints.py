"""privacy-safe transparency checkpoints

Revision ID: 20260727_0071
Revises: 20260726_0070
"""

from alembic import op
import sqlalchemy as sa

revision = "20260727_0071"
down_revision = "20260726_0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transparency_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checkpoint_id", sa.String(128), nullable=False),
        sa.Column("checkpoint_type", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_epoch", sa.Integer(), nullable=False),
        sa.Column("crypto_epoch", sa.Integer(), nullable=False),
        sa.Column("policy_epoch", sa.Integer(), nullable=False),
        sa.Column("issuer_key_id", sa.String(120), nullable=False),
        sa.Column("hash_suite", sa.String(30), nullable=False),
        sa.Column("signature_suite", sa.String(50), nullable=False),
        sa.Column("visibility", sa.String(40), nullable=False),
        sa.Column("stream_id_hash", sa.String(128), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("batch_identity_hash", sa.String(128), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("batch_start_time", sa.DateTime(), nullable=False),
        sa.Column("batch_end_time", sa.DateTime(), nullable=False),
        sa.Column("root_hash", sa.String(128), nullable=False),
        sa.Column("previous_checkpoint_hash", sa.String(128), nullable=False),
        sa.Column("checkpoint_hash", sa.String(128), nullable=False),
        sa.Column("metadata_commitment", sa.String(128), nullable=True),
        sa.Column("issuer_envelope_json", sa.JSON(), nullable=False),
        sa.Column("post_quantum_signature_json", sa.JSON(), nullable=True),
        sa.Column("publication_status", sa.String(30), nullable=False),
        sa.Column("verification_status", sa.String(30), nullable=False),
        sa.Column("signed_payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("supersedes_checkpoint_id", sa.String(128), nullable=True),
        sa.UniqueConstraint("checkpoint_id", name="uq_transparency_checkpoint_id"),
        sa.UniqueConstraint("checkpoint_hash", name="uq_transparency_checkpoint_hash"),
        sa.UniqueConstraint("stream_id_hash", "sequence_number", name="uq_transparency_stream_sequence"),
        sa.UniqueConstraint("batch_identity_hash", name="uq_transparency_batch_identity"),
    )
    for name, columns in (
        ("ix_transparency_checkpoint_type", ["checkpoint_type"]),
        ("ix_transparency_checkpoint_created", ["created_at"]),
        ("ix_transparency_checkpoint_publication", ["publication_status"]),
        ("ix_transparency_checkpoint_verification", ["verification_status"]),
    ):
        op.create_index(name, "transparency_checkpoints", columns)
    op.create_table(
        "transparency_checkpoint_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checkpoint_id", sa.String(128), sa.ForeignKey("transparency_checkpoints.checkpoint_id"), nullable=False),
        sa.Column("leaf_index", sa.Integer(), nullable=False),
        sa.Column("leaf_type", sa.String(80), nullable=False),
        sa.Column("leaf_hash", sa.String(128), nullable=False),
        sa.Column("object_commitment", sa.String(128), nullable=False),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("checkpoint_id", "leaf_index", name="uq_transparency_source_index"),
    )
    op.create_index("ix_transparency_source_checkpoint", "transparency_checkpoint_sources", ["checkpoint_id"])


def downgrade() -> None:
    op.drop_table("transparency_checkpoint_sources")
    op.drop_table("transparency_checkpoints")
