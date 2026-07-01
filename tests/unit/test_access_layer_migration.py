from __future__ import annotations

import importlib
from collections.abc import Iterator
from contextlib import contextmanager

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Connection

MIGRATION_MODULE = "app.db.migrations.versions.20260701_0063_access_layer_tables"

ACCESS_TABLES = {
    "access_payment_intents",
    "access_certificates",
    "subscription_entitlements",
    "access_devices",
    "access_challenges",
    "access_sessions",
    "access_request_nonces",
    "access_revocations",
    "access_audit_events",
    "metric_usage",
    "child_api_keys",
    "delegated_passes",
    "recovery_quorums",
    "recovery_attempts",
}

FORBIDDEN_COLUMNS = {
    "password",
    "password_hash",
    "raw_access_pass",
    "raw_session_token",
    "raw_recovery_seed",
    "bitcoin_seed",
    "bitcoin_private_key",
    "backend_private_key",
    "bearer_token",
}


@contextmanager
def _migration_ops(connection: Connection) -> Iterator[Operations]:
    context = MigrationContext.configure(connection)
    yield Operations(context)


def _run_upgrade(connection: Connection) -> None:
    migration = importlib.import_module(MIGRATION_MODULE)
    with _migration_ops(connection) as operations:
        original_op = migration.op
        migration.op = operations
        try:
            migration.upgrade()
        finally:
            migration.op = original_op


def _run_downgrade(connection: Connection) -> None:
    migration = importlib.import_module(MIGRATION_MODULE)
    with _migration_ops(connection) as operations:
        original_op = migration.op
        migration.op = operations
        try:
            migration.downgrade()
        finally:
            migration.op = original_op


def test_access_layer_migration_upgrade_creates_required_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        inspector = inspect(connection)

        assert ACCESS_TABLES.issubset(set(inspector.get_table_names()))


def test_access_layer_migration_has_no_forbidden_secret_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        inspector = inspect(connection)

        for table_name in ACCESS_TABLES:
            column_names = {column["name"] for column in inspector.get_columns(table_name)}
            assert column_names.isdisjoint(FORBIDDEN_COLUMNS), table_name


def test_access_layer_migration_creates_security_critical_indexes_and_uniques() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        inspector = inspect(connection)

        certificate_uniques = {
            tuple(unique["column_names"])
            for unique in inspector.get_unique_constraints("access_certificates")
        }
        nonce_uniques = {
            tuple(unique["column_names"])
            for unique in inspector.get_unique_constraints("access_request_nonces")
        }
        session_uniques = {
            tuple(unique["column_names"])
            for unique in inspector.get_unique_constraints("access_sessions")
        }
        indexes_by_table = {
            table_name: {index["name"] for index in inspector.get_indexes(table_name)}
            for table_name in ACCESS_TABLES
        }

        assert ("certificate_fingerprint",) in certificate_uniques
        assert ("pass_lookup_hash",) in certificate_uniques
        assert ("access_session_id", "nonce_hash") in nonce_uniques
        assert ("session_hash",) in session_uniques
        assert "ix_access_certificates_pass_lookup_hash" in indexes_by_table["access_certificates"]
        assert "ix_access_sessions_session_hash" in indexes_by_table["access_sessions"]
        assert "ix_access_revocations_target_hash" in indexes_by_table["access_revocations"]
        assert "ix_access_audit_events_event_hash" in indexes_by_table["access_audit_events"]
        assert "ix_child_api_keys_key_id_hash" in indexes_by_table["child_api_keys"]
        assert "ix_delegated_passes_delegated_pass_hash" in indexes_by_table["delegated_passes"]
        assert "ix_recovery_attempts_attempt_hash" in indexes_by_table["recovery_attempts"]


def test_access_layer_migration_downgrade_drops_required_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        _run_downgrade(connection)
        inspector = inspect(connection)

        assert ACCESS_TABLES.isdisjoint(set(inspector.get_table_names()))
