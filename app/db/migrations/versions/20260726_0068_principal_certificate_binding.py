"""principal-bound Access Certificate bridge

Revision ID: 20260726_0068
Revises: 20260726_0067
"""

from alembic import op
import sqlalchemy as sa

revision = "20260726_0068"
down_revision = "20260726_0067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_certificate_principal_bindings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("certificate_id", sa.Integer(), nullable=False),
        sa.Column("certificate_fingerprint", sa.String(128), nullable=False),
        sa.Column("principal_hash", sa.String(128), nullable=False),
        sa.Column("principal_type", sa.String(60), nullable=False),
        sa.Column("principal_binding_hash", sa.String(128), nullable=False),
        sa.Column("proof_method", sa.String(60), nullable=False),
        sa.Column("verification_strength", sa.String(40), nullable=False),
        sa.Column("device_key_fingerprint", sa.String(128), nullable=False),
        sa.Column("entitlement_fingerprint", sa.String(128), nullable=False),
        sa.Column("assurance_profile", sa.String(40), nullable=False),
        sa.Column("policy_epoch", sa.Integer(), nullable=False),
        sa.Column("principal_revocation_epoch", sa.Integer(), nullable=False),
        sa.Column("crypto_epoch", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["certificate_id"], ["access_certificates.id"]),
        sa.UniqueConstraint("certificate_id", name="uq_access_certificate_principal_binding_cert"),
        sa.UniqueConstraint(
            "principal_binding_hash", name="uq_access_certificate_principal_binding_hash"
        ),
    )
    for name in (
        "certificate_id",
        "certificate_fingerprint",
        "principal_hash",
        "principal_binding_hash",
        "device_key_fingerprint",
        "entitlement_fingerprint",
        "assurance_profile",
        "status",
    ):
        op.create_index(
            f"ix_access_certificate_principal_bindings_{name}",
            "access_certificate_principal_bindings",
            [name],
        )
    op.create_index(
        "ix_access_certificate_binding_principal_status",
        "access_certificate_principal_bindings",
        ["principal_hash", "status"],
    )


def downgrade() -> None:
    op.drop_table("access_certificate_principal_bindings")
