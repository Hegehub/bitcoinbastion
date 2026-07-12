"""wallet auth challenges

Revision ID: 20260712_0066
Revises: 20260709_0065
Create Date: 2026-07-12

Creates the Wallet-first challenge persistence table. The table stores hashes,
fingerprints, status, timestamps, canonical intent JSON, and redacted metadata;
it does not store raw wallet private keys, seeds, mnemonics, xprv, raw session
secrets, raw recovery material, passwords, mandatory email, global user_id, or
raw wallet signatures.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

from app.db.models.wallet_auth import WalletAuthChallenge

revision = "20260712_0066"
down_revision = "20260709_0065"
branch_labels = None
depends_on = None

WALLET_LNURL_TABLE_NAMES = (WalletAuthChallenge.__table__.name,)


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(WalletAuthChallenge.__table__.name):
        WalletAuthChallenge.__table__.create(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if _table_exists(WalletAuthChallenge.__table__.name):
        WalletAuthChallenge.__table__.drop(bind)
