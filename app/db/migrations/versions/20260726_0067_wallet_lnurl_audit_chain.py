"""wallet and LNURL canonical audit chain envelope

Revision ID: 20260726_0067
Revises: 20260712_0066
"""

from alembic import op
import sqlalchemy as sa

revision = "20260726_0067"
down_revision = "20260712_0066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("access_audit_events") as batch:
        batch.add_column(
            sa.Column("event_version", sa.Integer(), nullable=False, server_default="1")
        )
        batch.add_column(
            sa.Column("chain_id", sa.String(80), nullable=False, server_default="access-security")
        )
        batch.add_column(sa.Column("sequence_number", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("idempotency_key_hash", sa.String(128), nullable=True))
        batch.add_column(
            sa.Column("event_category", sa.String(40), nullable=False, server_default="security")
        )
        batch.add_column(
            sa.Column("event_status", sa.String(30), nullable=False, server_default="success")
        )
        batch.add_column(
            sa.Column("severity", sa.String(20), nullable=False, server_default="info")
        )
        batch.add_column(
            sa.Column("retention_class", sa.String(30), nullable=False, server_default="security")
        )
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM access_audit_events ORDER BY id")).fetchall()
    for sequence, row in enumerate(rows, start=1):
        connection.execute(
            sa.text("UPDATE access_audit_events SET sequence_number=:sequence WHERE id=:id"),
            {"sequence": sequence, "id": row[0]},
        )
    with op.batch_alter_table("access_audit_events") as batch:
        batch.alter_column("sequence_number", nullable=False)
        batch.create_unique_constraint(
            "uq_access_audit_chain_sequence", ["chain_id", "sequence_number"]
        )
        batch.create_unique_constraint(
            "uq_access_audit_chain_idempotency", ["chain_id", "idempotency_key_hash"]
        )
        for name in (
            "chain_id",
            "sequence_number",
            "idempotency_key_hash",
            "event_category",
            "event_status",
            "severity",
            "retention_class",
        ):
            batch.create_index(f"ix_access_audit_events_{name}", [name])


def downgrade() -> None:
    with op.batch_alter_table("access_audit_events") as batch:
        for name in (
            "chain_id",
            "sequence_number",
            "idempotency_key_hash",
            "event_category",
            "event_status",
            "severity",
            "retention_class",
        ):
            batch.drop_index(f"ix_access_audit_events_{name}")
        batch.drop_constraint("uq_access_audit_chain_idempotency", type_="unique")
        batch.drop_constraint("uq_access_audit_chain_sequence", type_="unique")
        for name in (
            "retention_class",
            "severity",
            "event_status",
            "event_category",
            "idempotency_key_hash",
            "sequence_number",
            "chain_id",
            "event_version",
        ):
            batch.drop_column(name)
