"""offline validity packs

Revision ID: 20260726_0069
Revises: 20260726_0068
"""

from alembic import op
import sqlalchemy as sa

revision = "20260726_0069"
down_revision = "20260726_0068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "offline_validity_packs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pack_id_hash", sa.String(128), nullable=False),
        sa.Column("pack_fingerprint", sa.String(128), nullable=False),
        sa.Column("principal_hash", sa.String(128), nullable=False),
        sa.Column("principal_type", sa.String(60), nullable=False),
        sa.Column("device_key_fingerprint", sa.String(128), nullable=False),
        sa.Column("access_certificate_fingerprint", sa.String(128), nullable=True),
        sa.Column("entitlement_fingerprint", sa.String(128), nullable=False),
        sa.Column("profile", sa.String(60), nullable=False),
        sa.Column("policy_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("signed_pack_json", sa.JSON(), nullable=False),
        sa.Column("revocation_epoch", sa.Integer(), nullable=False),
        sa.Column("policy_epoch", sa.Integer(), nullable=False),
        sa.Column("crypto_epoch", sa.Integer(), nullable=False),
        sa.Column("entitlement_epoch", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("not_before", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("reconcile_before", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("issuer_key_id", sa.String(120), nullable=False),
        sa.Column("signature_suite", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("pack_id_hash", name="uq_offline_validity_pack_id_hash"),
        sa.UniqueConstraint("pack_fingerprint", name="uq_offline_validity_pack_fingerprint"),
    )
    for name in (
        "pack_id_hash",
        "pack_fingerprint",
        "principal_hash",
        "device_key_fingerprint",
        "access_certificate_fingerprint",
        "entitlement_fingerprint",
        "profile",
        "expires_at",
        "reconcile_before",
        "status",
        "issuer_key_id",
    ):
        op.create_index(f"ix_offline_validity_packs_{name}", "offline_validity_packs", [name])
    op.create_index(
        "ix_offline_pack_principal_status", "offline_validity_packs", ["principal_hash", "status"]
    )
    op.create_table(
        "offline_pack_reconciliations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pack_id", sa.Integer(), nullable=False),
        sa.Column("event_chain_root", sa.String(128), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("reconciliation_status", sa.String(60), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("audit_event_hash", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["pack_id"], ["offline_validity_packs.id"]),
        sa.UniqueConstraint("pack_id", "event_chain_root", name="uq_offline_reconcile_pack_root"),
    )
    for name in ("pack_id", "event_chain_root", "reconciliation_status"):
        op.create_index(
            f"ix_offline_pack_reconciliations_{name}", "offline_pack_reconciliations", [name]
        )
    op.create_table(
        "offline_pack_local_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pack_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("previous_event_hash", sa.String(128), nullable=False),
        sa.Column("event_hash", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("safe_details_json", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pack_id"], ["offline_validity_packs.id"]),
        sa.UniqueConstraint("pack_id", "sequence_number", name="uq_offline_local_event_sequence"),
        sa.UniqueConstraint("event_hash"),
    )
    for name in ("pack_id", "event_hash", "event_type", "reconciled_at"):
        op.create_index(f"ix_offline_pack_local_events_{name}", "offline_pack_local_events", [name])


def downgrade() -> None:
    op.drop_table("offline_pack_local_events")
    op.drop_table("offline_pack_reconciliations")
    op.drop_table("offline_validity_packs")
