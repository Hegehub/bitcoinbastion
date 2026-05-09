from sqlalchemy import Column, Integer, MetaData, String, Table, text

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
        Column("name", String, server_default=text("'anon'")),
    )

    uniques = _model_unique_signature(table)
    assert (None, ("slug",)) in uniques
