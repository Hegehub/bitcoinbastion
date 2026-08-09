"""General, deterministic OpenAPI schema normalization for transport generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

JsonSchema = dict[str, object]


class SchemaCompileError(ValueError):
    pass


@dataclass(frozen=True)
class CompiledSchema:
    kind: str


@dataclass(frozen=True)
class PrimitiveSchema(CompiledSchema):
    primitive: Literal["string", "integer", "number", "boolean"]
    format: str | None = None
    constraints: tuple[tuple[str, object], ...] = ()


@dataclass(frozen=True)
class NullSchema(CompiledSchema):
    pass


@dataclass(frozen=True)
class ReferenceSchema(CompiledSchema):
    component: str


@dataclass(frozen=True)
class ArraySchema(CompiledSchema):
    items: CompiledSchema
    constraints: tuple[tuple[str, object], ...] = ()


@dataclass(frozen=True)
class UnionSchema(CompiledSchema):
    branches: tuple[CompiledSchema, ...]


@dataclass(frozen=True)
class LiteralSchema(CompiledSchema):
    values: tuple[object, ...]


@dataclass(frozen=True)
class MapSchema(CompiledSchema):
    values: CompiledSchema
    arbitrary_json: bool = False


@dataclass(frozen=True)
class PropertySchema:
    name: str
    schema: CompiledSchema
    required: bool


@dataclass(frozen=True)
class ObjectSchema(CompiledSchema):
    properties: tuple[PropertySchema, ...]
    additional: Literal["forbid"] | MapSchema


@dataclass(frozen=True)
class JsonValueSchema(CompiledSchema):
    """Explicit valid-JSON recursion; never arbitrary Python object."""


_CONSTRAINTS = (
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength",
    "maxLength", "pattern", "minItems", "maxItems",
)


class OpenAPISchemaCompiler:
    def __init__(self, components: dict[str, JsonSchema]) -> None:
        self.components = dict(sorted(components.items()))

    def compile_component(self, name: str) -> CompiledSchema:
        try:
            schema = self.components[name]
        except KeyError as exc:
            raise SchemaCompileError(f"unresolved component: {name}") from exc
        return self.compile(schema, location=f"components.schemas.{name}")

    def compile(self, schema: JsonSchema, *, location: str) -> CompiledSchema:
        semantic_keys = set(schema) - {"title", "description", "examples", "default"}
        if not semantic_keys:
            # An empty OpenAPI schema is the specification's arbitrary-JSON
            # vocabulary. Keep it JSON-bounded rather than degrading to Any.
            return JsonValueSchema("json-value")
        reference = schema.get("$ref")
        if isinstance(reference, str):
            prefix = "#/components/schemas/"
            if not reference.startswith(prefix):
                raise SchemaCompileError(f"{location}: unsupported reference {reference}")
            name = reference.removeprefix(prefix)
            if name not in self.components:
                raise SchemaCompileError(f"{location}: unresolved component {name}")
            return ReferenceSchema("reference", name)

        any_of = schema.get("anyOf")
        if isinstance(any_of, list):
            if not any_of:
                raise SchemaCompileError(f"{location}: empty anyOf")
            return UnionSchema(
                "union",
                tuple(
                    self.compile(
                        self._schema(branch, f"{location}.anyOf[{index}]"),
                        location=f"{location}.anyOf[{index}]",
                    )
                    for index, branch in enumerate(any_of)
                ),
            )

        enum = schema.get("enum")
        if isinstance(enum, list):
            return LiteralSchema("literal", tuple(enum))
        if "const" in schema:
            return LiteralSchema("literal", (schema["const"],))

        schema_type = schema.get("type")
        if schema_type == "null":
            return NullSchema("null")
        if schema_type in {"string", "integer", "number", "boolean"}:
            raw_format = schema.get("format")
            schema_format = raw_format if isinstance(raw_format, str) else None
            return PrimitiveSchema(
                "primitive",
                schema_type,  # type: ignore[arg-type]
                schema_format,
                self._constraints(schema),
            )
        if schema_type == "array":
            items = self._schema(schema.get("items"), f"{location}.items")
            return ArraySchema(
                "array",
                self.compile(items, location=f"{location}.items"),
                self._constraints(schema),
            )
        if schema_type == "object" or "properties" in schema or "additionalProperties" in schema:
            return self._compile_object(schema, location)
        raise SchemaCompileError(f"{location}: unsupported schema keys {sorted(schema)}")

    def compile_all(self) -> dict[str, CompiledSchema]:
        return {name: self.compile_component(name) for name in self.components}

    def dependency_graph(self) -> dict[str, tuple[str, ...]]:
        graph: dict[str, tuple[str, ...]] = {}
        for name, schema in self.components.items():
            refs: set[str] = set()
            self._collect_refs(schema, refs)
            graph[name] = tuple(sorted(refs))
        return graph

    def cycles(self) -> tuple[tuple[str, ...], ...]:
        graph = self.dependency_graph()
        cycles: set[tuple[str, ...]] = set()
 
        def visit(node: str, path: tuple[str, ...]) -> None:
            if node in path:
                cycle = path[path.index(node):]
                rotations = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
                cycles.add(min(rotations))
                return
            for dependency in graph[node]:
                visit(dependency, path + (node,))

        for component in graph:
            visit(component, ())
        return tuple(sorted(cycles))

    def _compile_object(self, schema: JsonSchema, location: str) -> ObjectSchema:
        raw_properties = schema.get("properties", {})
        if not isinstance(raw_properties, dict):
            raise SchemaCompileError(f"{location}: properties must be an object")
        required_value = schema.get("required", [])
        required = set(required_value) if isinstance(required_value, list) else set()
        properties = tuple(
            PropertySchema(
                str(name),
                self.compile(
                    self._schema(value, f"{location}.properties.{name}"),
                    location=f"{location}.properties.{name}",
                ),
                name in required,
            )
            for name, value in sorted(raw_properties.items())
        )
        additional_value = schema.get("additionalProperties", False)
        if additional_value is False:
            additional: Literal["forbid"] | MapSchema = "forbid"
        elif additional_value is True:
            additional = MapSchema("map", JsonValueSchema("json-value"), arbitrary_json=True)
        else:
            additional_schema = self._schema(additional_value, f"{location}.additionalProperties")
            additional = MapSchema(
                "map",
                self.compile(additional_schema, location=f"{location}.additionalProperties"),
            )
        return ObjectSchema("object", properties, additional)

    @staticmethod
    def _schema(value: object, location: str) -> JsonSchema:
        if not isinstance(value, dict):
            raise SchemaCompileError(f"{location}: expected schema object")
        return value

    @staticmethod
    def _constraints(schema: JsonSchema) -> tuple[tuple[str, object], ...]:
        return tuple((key, schema[key]) for key in _CONSTRAINTS if key in schema)

    @classmethod
    def _collect_refs(cls, value: object, refs: set[str]) -> None:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/components/schemas/"):
                refs.add(reference.rsplit("/", 1)[-1])
            for child in value.values():
                cls._collect_refs(child, refs)
        elif isinstance(value, list):
            for child in value:
                cls._collect_refs(child, refs)
