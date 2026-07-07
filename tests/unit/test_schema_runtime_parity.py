from sqlalchemy import Column, Integer, MetaData, String, Table

from scripts.check_schema_runtime_parity import (
    _model_unique_signature,
    _normalize_default,
    _types_have_same_affinity,
)


def test_types_have_same_affinity_for_equivalent_integers() -> None:
    assert _types_have_same_affinity(Integer(), Integer())


def test_types_have_same_affinity_rejects_different_affinity() -> None:
    assert not _types_have_same_affinity(Integer(), String())


def test_types_have_same_affinity_rejects_non_type_engine() -> None:
    assert not _types_have_same_affinity(Integer(), "INTEGER")


def test_normalize_default_removes_wrapper_and_whitespace() -> None:
    assert _normalize_default(" ( CURRENT_TIMESTAMP ) ") == "current_timestamp"


def test_model_unique_signature_includes_column_unique_flags() -> None:
    table = Table(
        "example",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("slug", String, unique=True),
        Column("name", String, server_default="anon"),
    )

    uniques = _model_unique_signature(table)
    assert (None, ("slug",)) in uniques


class _InspectorStub:
    def __init__(self) -> None:
        self._tables = ["example"]

    def get_table_names(self) -> list[str]:
        return self._tables

    def get_columns(self, table_name: str) -> list[dict[str, object]]:
        assert table_name == "example"
        return [
            {"name": "id", "nullable": False, "type": Integer(), "default": None},
            {"name": "slug", "nullable": True, "type": String(), "default": "'x'"},
        ]

    def get_indexes(self, table_name: str) -> list[dict[str, object]]:
        return [{"name": "ix_example_slug", "column_names": ["slug"], "unique": False}]

    def get_unique_constraints(self, table_name: str) -> list[dict[str, object]]:
        return [{"name": "uq_example_slug", "column_names": ["slug"]}]

    def get_foreign_keys(self, table_name: str) -> list[dict[str, object]]:
        return []


def test_collect_schema_parity_errors_surfaces_column_nullable_default_and_index_drift(
    monkeypatch,
) -> None:
    from scripts import check_schema_runtime_parity as parity

    metadata = MetaData()
    Table(
        "example",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("slug", String, nullable=False, unique=True, server_default="anon"),
    )

    monkeypatch.setattr(parity.Base, "metadata", metadata)
    errors = parity.collect_schema_parity_errors(_InspectorStub())

    assert any(err.startswith("nullable parity mismatch:") for err in errors)
    assert any(err.startswith("default parity mismatch:") for err in errors)
    assert any(err.startswith("index parity mismatch:") for err in errors)
