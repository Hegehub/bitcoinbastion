"""disaster recovery validation records

Revision ID: 20260605_0051
Revises: 20260605_0050
Create Date: 2026-06-05 00:51:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260605_0051"
down_revision = "20260605_0050"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "backup_validation_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backup_id", sa.String(length=160), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("objects_checked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("integrity_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("limitations", json_type, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_backup_validation_records_backup_id", "backup_validation_records", ["backup_id"]
    )
    op.create_index(
        "ix_backup_validation_records_started_at", "backup_validation_records", ["started_at"]
    )
    op.create_index(
        "ix_backup_validation_records_success", "backup_validation_records", ["success"]
    )
    op.create_index(
        "ix_backup_validation_records_integrity_verified",
        "backup_validation_records",
        ["integrity_verified"],
    )
    op.create_index(
        "ix_backup_validation_records_created_at", "backup_validation_records", ["created_at"]
    )

    op.create_table(
        "recovery_validation_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recovery_id", sa.String(length=160), nullable=False),
        sa.Column("validation_type", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "deterministic_rebuild_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("integrity_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("replay_types", json_type, nullable=False, server_default="[]"),
        sa.Column("limitations", json_type, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_recovery_validation_records_recovery_id", "recovery_validation_records", ["recovery_id"]
    )
    op.create_index(
        "ix_recovery_validation_records_validation_type",
        "recovery_validation_records",
        ["validation_type"],
    )
    op.create_index(
        "ix_recovery_validation_records_started_at", "recovery_validation_records", ["started_at"]
    )
    op.create_index(
        "ix_recovery_validation_records_success", "recovery_validation_records", ["success"]
    )
    op.create_index(
        "ix_recovery_validation_records_created_at", "recovery_validation_records", ["created_at"]
    )


def downgrade() -> None:
    for index in [
        "ix_recovery_validation_records_created_at",
        "ix_recovery_validation_records_success",
        "ix_recovery_validation_records_started_at",
        "ix_recovery_validation_records_validation_type",
        "ix_recovery_validation_records_recovery_id",
    ]:
        op.drop_index(index, table_name="recovery_validation_records")
    op.drop_table("recovery_validation_records")
    for index in [
        "ix_backup_validation_records_created_at",
        "ix_backup_validation_records_integrity_verified",
        "ix_backup_validation_records_success",
        "ix_backup_validation_records_started_at",
        "ix_backup_validation_records_backup_id",
    ]:
        op.drop_index(index, table_name="backup_validation_records")
    op.drop_table("backup_validation_records")
