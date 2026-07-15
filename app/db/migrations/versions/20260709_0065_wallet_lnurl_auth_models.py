"""wallet lnurl auth models

Revision ID: 20260709_0065
Revises: 20260705_0064
Create Date: 2026-07-09

Creates the Wallet-first + LNURL Proof-of-Access Auth PQ v2 persistence
layer. The table metadata intentionally stores hashes, fingerprints,
commitments, and redacted JSON metadata only: no raw wallet private keys,
Bitcoin seeds, mnemonics, xprv, raw k1 values, raw session tokens, raw
Access Passes, raw recovery phrases, or global wallet user_id columns.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

from app.db.models.lnurl import (
    LNURLAuthAttempt,
    LNURLAuthChallenge,
    LNURLInvoice,
    LNURLPayRequest,
    LNURLPayerData,
    LNURLPaymentProof,
    LNURLPrincipal,
    LNURLReceiptPacket,
    LNURLSuccessAction,
    LNURLVerifyCheck,
    LNURLWithdrawAttempt,
    LNURLWithdrawRequest,
    LightningAddress,
    PayRegisterLNURLBinding,
)
from app.db.models.wallet_auth import (
    MultiWalletQuorum,
    RecoveryCapsule,
    WalletDevice,
    WalletPrincipal,
    WalletPrivacyCommitment,
    WalletProof,
    WalletSession,
    WalletSessionNonce,
    WalletStepUpProof,
)

revision = "20260709_0065"
down_revision = "20260705_0064"
branch_labels = None
depends_on = None

WALLET_LNURL_TABLES = (
    WalletPrincipal.__table__,
    WalletProof.__table__,
    WalletDevice.__table__,
    WalletSession.__table__,
    WalletSessionNonce.__table__,
    WalletStepUpProof.__table__,
    RecoveryCapsule.__table__,
    MultiWalletQuorum.__table__,
    WalletPrivacyCommitment.__table__,
    LNURLAuthChallenge.__table__,
    LNURLAuthAttempt.__table__,
    LNURLPrincipal.__table__,
    LNURLPayRequest.__table__,
    LNURLInvoice.__table__,
    LNURLPaymentProof.__table__,
    LNURLVerifyCheck.__table__,
    LNURLWithdrawRequest.__table__,
    LNURLWithdrawAttempt.__table__,
    LNURLSuccessAction.__table__,
    LNURLPayerData.__table__,
    LightningAddress.__table__,
    LNURLReceiptPacket.__table__,
    PayRegisterLNURLBinding.__table__,
)

WALLET_LNURL_TABLE_NAMES = tuple(table.name for table in WALLET_LNURL_TABLES)


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()
    for table in WALLET_LNURL_TABLES:
        if not _table_exists(table.name):
            table.create(bind)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(WALLET_LNURL_TABLES):
        if _table_exists(table.name):
            table.drop(bind)
