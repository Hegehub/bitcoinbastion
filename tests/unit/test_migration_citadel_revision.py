from pathlib import Path


def test_citadel_migration_revision_exists() -> None:
    migration_path = Path("app/db/migrations/versions/20260416_0007_citadel_assessments.py")
    assert migration_path.exists()

    contents = migration_path.read_text()
    assert 'revision = "20260416_0007"' in contents
    assert 'down_revision = "20260414_0006"' in contents
    assert "citadel_assessments" in contents
