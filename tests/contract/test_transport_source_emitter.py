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
