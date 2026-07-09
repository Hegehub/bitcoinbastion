"""Safety checks for the Wallet-first + LNURL Alembic migration."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

MIGRATION_PATH = Path("app/db/migrations/versions/20260709_0065_wallet_lnurl_auth_models.py")
FORBIDDEN_COLUMN_FRAGMENTS = ("private_key", "seed", "mnemonic", "xprv")
WALLET_LNURL_TABLES = {
    "wallet_principals",
    "bitcoin_wallet_proofs",
    "lightning_principals",
    "wallet_devices",
    "wallet_sessions",
    "wallet_session_nonces",
    "wallet_step_up_proofs",
    "wallet_privacy_commitments",
    "recovery_capsules",
    "multi_wallet_quorums",
    "lnurl_auth_challenges",
    "lnurl_auth_attempts",
    "lnurl_pay_requests",
    "lnurl_payment_proofs",
    "lnurl_verify_checks",
    "lnurl_success_actions",
    "lnurl_payer_data",
    "lightning_addresses",
    "lnurl_withdraw_requests",
    "lnurl_withdraw_attempts",
    "lnurl_receipt_packets",
    "payregister_lnurl_terminals",
}


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("wallet_lnurl_auth_models", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_module_imports_and_has_downgrade() -> None:
    migration = _load_migration()
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


def test_required_wallet_lnurl_tables_are_declared() -> None:
    migration = _load_migration()
    assert WALLET_LNURL_TABLES.issubset(set(migration.WALLET_LNURL_TABLE_NAMES))


def test_no_forbidden_secret_or_global_user_id_columns() -> None:
    migration = _load_migration()
    for table in migration.WALLET_LNURL_TABLES:
        for column in table.columns:
            assert column.name != "user_id", (table.name, column.name)
            assert all(fragment not in column.name for fragment in FORBIDDEN_COLUMN_FRAGMENTS), (table.name, column.name)


def test_hash_first_security_columns_are_declared() -> None:
    migration = _load_migration()
    tables = {table.name: {column.name for column in table.columns} for table in migration.WALLET_LNURL_TABLES}

    assert "session_hash" in tables["wallet_sessions"]
    assert "session_token" not in tables["wallet_sessions"]
    assert "k1_hash" in tables["lnurl_auth_challenges"]
    assert "k1" not in tables["lnurl_auth_challenges"]
    assert "lnurl_key_hash" in tables["lightning_principals"]
    assert "linking_key" not in tables["lightning_principals"]
    assert {"invoice_hash", "payment_hash"}.issubset(tables["lnurl_payment_proofs"])
    assert "invoice_payload" not in tables["lnurl_payment_proofs"]
    assert "recovery_phrase" not in tables["recovery_capsules"]
