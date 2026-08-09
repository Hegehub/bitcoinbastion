"""Deterministic Python source emission for normalized transport schemas.

This module deliberately knows nothing about OpenAPI dictionaries.  Schema
semantics belong to :mod:`schema_compiler`; the emitter only renders its IR.
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass

from .schema_compiler import (
    ArraySchema,
    CompiledSchema,
    JsonValueSchema,
    LiteralSchema,
    MapSchema,
    NullSchema,
    ObjectSchema,
    PrimitiveSchema,
    ReferenceSchema,
    UnionSchema,
)


class SourceEmissionError(ValueError):
    """Raised when normalized IR cannot be represented without weakening it."""


@dataclass(frozen=True)
class ModulePlan:
    components: tuple[tuple[str, CompiledSchema], ...]

    @classmethod
    def build(cls, components: dict[str, CompiledSchema]) -> ModulePlan:
        symbols: dict[str, str] = {}
        for canonical in sorted(components):
            symbol = python_symbol(canonical)
            previous = symbols.setdefault(symbol, canonical)
            if previous != canonical:
                raise SourceEmissionError(
                    f"symbol collision: {previous!r} and {canonical!r} become {symbol!r}"
                )
        return cls(tuple((name, components[name]) for name in sorted(components)))


def python_symbol(value: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    symbol = "".join(part[:1].upper() + part[1:] for part in parts) or "GeneratedType"
    if symbol[0].isdigit():
        symbol = f"Schema{symbol}"
    return symbol


def field_symbol(value: str) -> str:
    symbol = re.sub(r"\W", "_", value)
    if not symbol or symbol[0].isdigit() or keyword.iskeyword(symbol):
        symbol = f"field_{symbol}"
    return symbol


def emit_annotation(schema: CompiledSchema) -> str:
    if isinstance(schema, PrimitiveSchema):
        if schema.primitive == "string":
            return {"date-time": "datetime", "date": "date", "uuid": "UUID"}.get(
                schema.format or "", "str"
            )
        return {"integer": "int", "number": "Decimal", "boolean": "bool"}[
            schema.primitive
        ]
    if isinstance(schema, NullSchema):
        return "None"
    if isinstance(schema, ReferenceSchema):
        return python_symbol(schema.component)
    if isinstance(schema, ArraySchema):
        return f"list[{emit_annotation(schema.items)}]"
    if isinstance(schema, MapSchema):
        value = "JsonValue" if schema.arbitrary_json else emit_annotation(schema.values)
        return f"dict[str, {value}]"
    if isinstance(schema, JsonValueSchema):
        return "JsonValue"
    if isinstance(schema, LiteralSchema):
        return "Literal[" + ", ".join(repr(value) for value in schema.values) + "]"
    if isinstance(schema, UnionSchema):
        rendered = tuple(dict.fromkeys(emit_annotation(branch) for branch in schema.branches))
        return " | ".join(rendered)
    if isinstance(schema, ObjectSchema):
        if not schema.properties and isinstance(schema.additional, MapSchema):
            return emit_annotation(schema.additional)
        if not schema.properties and schema.additional == "forbid":
            return "dict[str, Never]"
        raise SourceEmissionError("inline object requires a canonical module-plan identity")
    raise SourceEmissionError(f"unsupported compiled schema {type(schema).__name__}")


def emit_module(plan: ModulePlan) -> str:
    lines = [
        '"""Generated strict HTTP transport models. Do not edit."""',
        "from __future__ import annotations",
        "",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import Literal, Never",
        "from uuid import UUID",
        "",
        "from pydantic import BaseModel, ConfigDict, Field, RootModel",
        "",
        "type JsonValue = (None | bool | int | Decimal | str",
        "    | list[JsonValue] | dict[str, JsonValue])",
        "",
    ]
    for canonical, schema in plan.components:
        name = python_symbol(canonical)
        if isinstance(schema, ObjectSchema):
            lines.append(f"class {name}(BaseModel):")
            lines.append("    model_config = ConfigDict(extra='forbid', strict=True)")
            if not schema.properties:
                lines.append("    pass")
            for prop in schema.properties:
                annotation = emit_annotation(prop.schema)
                py_name = field_symbol(prop.name)
                alias = "" if py_name == prop.name else f", alias={prop.name!r}"
                if prop.required:
                    default = f"Field(...{alias})" if alias else ""
                else:
                    # Absence is represented by the default; explicit null remains
                    # governed by whether the compiled annotation contains None.
                    default = f"Field(default=None{alias})"
                    if "None" not in annotation.split(" | "):
                        annotation = f"{annotation} | None"
                lines.append(f"    {py_name}: {annotation}" + (f" = {default}" if default else ""))
            lines.append("")
        else:
            lines.extend(
                [f"class {name}(RootModel[{emit_annotation(schema)}]):", "    pass", ""]
            )
    lines.extend([f"{python_symbol(name)}.model_rebuild()" for name, _ in plan.components])
    return "\n".join(lines) + "\n"
