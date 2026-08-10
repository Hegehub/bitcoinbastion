import pytest
from pydantic import ValidationError

from frontend.bastion_ui.transport.schema_compiler import OpenAPISchemaCompiler
from frontend.bastion_ui.transport.source_emitter import ModulePlan, emit_module


def test_emitter_is_deterministic_and_uses_datetime() -> None:
    compiler = OpenAPISchemaCompiler(
        {
            "AccessClock": {
                "type": "object",
                "properties": {
                    "expires_at": {"type": "string", "format": "date-time"},
                },
                "required": ["expires_at"],
            }
        }
    )
    plan = ModulePlan.build(compiler.compile_all())
    first = emit_module(plan)
    assert first == emit_module(plan)
    assert "expires_at: datetime" in first
    assert "Any" not in first
    compile(first, "generated_models.py", "exec")


def test_closed_empty_object_emits_as_strict_pydantic_model() -> None:
    compiler = OpenAPISchemaCompiler(
        {"Empty": {"type": "object", "properties": {}, "additionalProperties": False}}
    )
    namespace: dict[str, object] = {}
    exec(emit_module(ModulePlan.build(compiler.compile_all())), namespace)
    empty = namespace["Empty"]
    assert empty.model_validate({}).model_dump() == {}  # type: ignore[attr-defined]
    with pytest.raises(ValidationError):
        empty.model_validate({"x": 1})  # type: ignore[attr-defined]
