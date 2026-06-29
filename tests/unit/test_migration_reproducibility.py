from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def _snapshot_schema(database_url: str) -> dict[str, tuple[str, ...]]:
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    table_names = sorted(name for name in inspector.get_table_names() if name != "alembic_version")
    return {
        table_name: tuple(sorted(column["name"] for column in inspector.get_columns(table_name)))
        for table_name in table_names
    }


def test_migration_bootstrap_replay_and_deterministic_recreation(tmp_path) -> None:
    db_path = tmp_path / "reproducibility.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    cfg = _alembic_config(database_url)

    command.upgrade(cfg, "head")
    first_snapshot = _snapshot_schema(database_url)
    assert first_snapshot, "Expected non-empty schema after clean bootstrap upgrade to head"

    command.downgrade(cfg, "base")
    after_downgrade = _snapshot_schema(database_url)
    assert after_downgrade == {}, (
        "Expected empty schema after downgrade to base; "
        f"found residual tables={sorted(after_downgrade.keys())}"
    )

    command.upgrade(cfg, "head")
    second_snapshot = _snapshot_schema(database_url)

    assert second_snapshot == first_snapshot, (
        "Schema drift across replay detected; "
        f"first_tables={sorted(first_snapshot.keys())} second_tables={sorted(second_snapshot.keys())}"
    )
