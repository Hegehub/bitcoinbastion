from __future__ import annotations

import re
from pathlib import Path

from app.db.base import Base
import app.db.models  # noqa: F401

CREATE_TABLE_RE = re.compile(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]")
REVISION_RE = re.compile(r"^revision\s*=\s*[\'\"]([^\'\"]+)[\'\"]", re.MULTILINE)
DOWN_REVISION_RE = re.compile(r"^down_revision\s*=\s*(?:[\'\"]([^\'\"]+)[\'\"]|None)", re.MULTILINE)


def _migration_files() -> list[Path]:
    return sorted(Path("app/db/migrations/versions").glob("*.py"))


def test_models_and_migrations_have_identical_table_coverage() -> None:
    model_tables = set(Base.metadata.tables.keys())

    migration_tables: set[str] = set()
    for revision in _migration_files():
        migration_tables.update(CREATE_TABLE_RE.findall(revision.read_text()))

    assert model_tables == migration_tables


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
