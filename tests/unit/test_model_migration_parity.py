from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

from app.db.base import Base
import app.db.models  # noqa: F401

CREATE_TABLE_RE = re.compile(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]")
REVISION_RE = re.compile(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
DOWN_REVISION_RE = re.compile(r"^down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", re.MULTILINE)

MODEL_ONLY_TABLES_PENDING_MIGRATION = {
    # Prompt 5/72 intentionally adds model definitions before Prompt 6/72
    # creates the corresponding Alembic revision. These tables remain excluded
    # from strict model/migration parity until the migration prompt lands.
    "wallet_principals",
    "wallet_proofs",
    "wallet_devices",
    "wallet_sessions",
    "wallet_session_nonces",
    "wallet_step_up_proofs",
    "recovery_capsules",
    "multi_wallet_quorums",
    "wallet_privacy_commitments",
    "lnurl_auth_challenges",
    "lnurl_auth_attempts",
    "lnurl_principals",
    "lnurl_pay_requests",
    "lnurl_invoices",
    "lnurl_payment_proofs",
    "lnurl_verify_checks",
    "lnurl_withdraw_requests",
    "lnurl_withdraw_attempts",
    "lnurl_success_actions",
    "lnurl_payer_data",
    "lightning_addresses",
    "lnurl_receipt_packets",
    "payregister_lnurl_bindings",
}


def _migration_files() -> list[Path]:
    return sorted(Path("app/db/migrations/versions").glob("*.py"))


def _load_migration_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_models_and_migrations_have_identical_table_coverage() -> None:
    model_tables = set(Base.metadata.tables.keys())

    migration_tables: set[str] = set()
    for revision in _migration_files():
        contents = revision.read_text()
        migration_tables.update(CREATE_TABLE_RE.findall(contents))
        module = _load_migration_module(revision)
        migration_tables.update(getattr(module, "WALLET_LNURL_TABLE_NAMES", ()))

    assert model_tables - MODEL_ONLY_TABLES_PENDING_MIGRATION == migration_tables
    assert migration_tables <= model_tables


def test_migration_chain_has_single_head_and_valid_parent_links() -> None:
    revisions: set[str] = set()
    down_revisions: set[str] = set()

    for migration_file in _migration_files():
        contents = migration_file.read_text()

        revision_match = REVISION_RE.search(contents)
        assert revision_match is not None, f"Missing revision in {migration_file}"
        revision = revision_match.group(1)
        revisions.add(revision)

        down_match = DOWN_REVISION_RE.search(contents)
        assert down_match is not None, f"Missing down_revision in {migration_file}"
        down_revision = down_match.group(1)
        if down_revision:
            down_revisions.add(down_revision)

    assert len(revisions - down_revisions) == 1, "Migration graph must have exactly one head"
    assert (
        down_revisions - revisions == set()
    ), "All down_revision values must reference existing revisions"
