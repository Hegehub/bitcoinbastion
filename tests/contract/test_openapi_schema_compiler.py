from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "frontend"))

from app.main import app  # noqa: E402
from bastion_ui.transport.schema_compiler import (  # noqa: E402
    JsonValueSchema,
    MapSchema,
    NullSchema,
    ObjectSchema,
    OpenAPISchemaCompiler,
    SchemaCompileError,
    UnionSchema,
)


def test_runtime_components_fail_closed_on_backend_any_schemas() -> None:
    components = app.openapi()["components"]["schemas"]
    compiler = OpenAPISchemaCompiler(components)

    failures: dict[str, str] = {}
    compiled = {}
    for name in sorted(components):
        try:
            compiled[name] = compiler.compile_component(name)
        except SchemaCompileError as exc:
            failures[name] = str(exc)

    assert len(compiled) == 271
    assert len(failures) == 15
    assert set(failures) == {
        "AccessCertificateIssueResponse",
        "AccessChallengeResponse",
        "AccessLockdownResponse",
        "AccessMeResponse",
        "AccessPaymentIntentResponse",
        "AccessPaymentIntentStatusResponse",
        "AccessSessionResponse",
        "ChildApiKeyCreateResponse",
        "ChildApiKeyPublic",
        "DelegatedPassCreateResponse",
        "DelegatedPassPublic",
        "RecoveryStartResponse",
        "RecoveryStatusResponse",
        "SubscriptionEntitlementResponse",
        "ValidationError",
    }
    assert all("unsupported schema keys" in error for error in failures.values())
    assert len(compiler.dependency_graph()) == 286


def test_anyof_preserves_nullable_and_union_branches() -> None:
    compiler = OpenAPISchemaCompiler({})
    compiled = compiler.compile(
        {"anyOf": [{"type": "string"}, {"type": "null"}]}, location="test.nullable"
    )
    assert isinstance(compiled, UnionSchema)
    assert len(compiled.branches) == 2
    assert isinstance(compiled.branches[1], NullSchema)


def test_additional_properties_are_closed_typed_or_explicit_json() -> None:
    compiler = OpenAPISchemaCompiler({})
    closed = compiler.compile({"type": "object", "additionalProperties": False}, location="closed")
    typed = compiler.compile(
        {"type": "object", "additionalProperties": {"type": "integer"}}, location="typed"
    )
    arbitrary = compiler.compile(
        {"type": "object", "additionalProperties": True}, location="arbitrary"
    )

    assert isinstance(closed, ObjectSchema) and closed.additional == "forbid"
    assert isinstance(typed, ObjectSchema) and isinstance(typed.additional, MapSchema)
    assert isinstance(arbitrary, ObjectSchema) and isinstance(arbitrary.additional, MapSchema)
    assert isinstance(arbitrary.additional.values, JsonValueSchema)


def test_unresolved_and_unsupported_schemas_fail_explicitly() -> None:
    compiler = OpenAPISchemaCompiler({})
    with pytest.raises(SchemaCompileError, match="unresolved component"):
        compiler.compile({"$ref": "#/components/schemas/Missing"}, location="missing")
    with pytest.raises(SchemaCompileError, match="unsupported schema"):
        compiler.compile({}, location="empty")
