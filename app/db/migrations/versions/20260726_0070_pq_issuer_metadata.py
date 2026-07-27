"""shared issuer envelope metadata

Revision ID: 20260726_0070
Revises: 20260726_0069
"""

from alembic import op
import sqlalchemy as sa

revision = "20260726_0070"
down_revision = "20260726_0069"
branch_labels = None
depends_on = None

TABLES = (
    "access_certificates",
    "subscription_entitlements",
    "offline_validity_packs",
    "recovery_capsules",
    "lnurl_payment_proofs",
)


def upgrade() -> None:
    for table in TABLES:
        inspector = sa.inspect(op.get_bind())
        existing = {column["name"] for column in inspector.get_columns(table)}
        additions = (
            sa.Column("issuer_envelope_json", sa.JSON(), nullable=True),
            sa.Column("issuer_envelope_hash", sa.String(128), nullable=True),
            sa.Column("signature_requirement_policy", sa.String(60), nullable=True),
            sa.Column("crypto_assurance", sa.String(40), nullable=True),
            sa.Column("requires_reissue", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        for column in additions:
            if column.name not in existing:
                op.add_column(table, column)
        index_name = f"ix_{table}_issuer_envelope_hash"
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}
        if index_name not in indexes:
            op.create_index(index_name, table, ["issuer_envelope_hash"])
        op.execute(
            sa.text(
                f"UPDATE {table} SET requires_reissue = true WHERE issuer_envelope_json IS NULL"
            )
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_issuer_envelope_hash", table_name=table)
        op.drop_column(table, "requires_reissue")
        op.drop_column(table, "crypto_assurance")
        op.drop_column(table, "signature_requirement_policy")
        op.drop_column(table, "issuer_envelope_hash")
        op.drop_column(table, "issuer_envelope_json")
