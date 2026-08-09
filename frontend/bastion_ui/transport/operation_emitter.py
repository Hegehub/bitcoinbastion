"""Deterministic operation/client/ownership/Feature-53 source emission."""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass

from .operation_compiler import CompiledOperation
from .source_emitter import emit_annotation, field_symbol, python_symbol


@dataclass(frozen=True)
class OperationModulePlan:
    operations: tuple[CompiledOperation, ...]
    source_revision: str = "unknown"

    @classmethod
    def build(
        cls, operations: tuple[CompiledOperation, ...], *, source_revision: str = "unknown"
    ) -> OperationModulePlan:
        callable_names: set[str] = set()
        for operation in operations:
            if operation.callable_name in callable_names:
                raise ValueError(f"duplicate callable: {operation.callable_name}")
            callable_names.add(operation.callable_name)
        return cls(tuple(sorted(operations, key=lambda item: item.matrix_id)), source_revision)


def _success_symbol(operation: CompiledOperation) -> str:
    return f"{python_symbol(operation.operation_id)}Success"


def _request_symbol(operation: CompiledOperation) -> str:
    return f"{python_symbol(operation.operation_id)}Request"


def emit_operations(plan: OperationModulePlan) -> str:
    lines = [
        '"""Generated typed HTTP operations. Do not edit."""',
        "# ruff: noqa",
        "from __future__ import annotations",
        "",
        "from datetime import datetime",
        "from decimal import Decimal",
        "from typing import Literal",
        "from pydantic import BaseModel, ConfigDict, RootModel",
        "",
        "from bastion_ui.transport.foundation import (",
        "    ContractRegistryEntry, HttpTransport, NormalizedOperation, SecurityMetadata,",
        "    serialize_query_value,",
        ")",
        "from bastion_ui.transport.generated_schemas import *  # noqa: F403",
        "",
        "class NoRequest(BaseModel):",
        "    model_config = ConfigDict(extra='forbid', frozen=True)",
        "",
    ]
    ownership: list[str] = []
    registry: list[str] = []
    for operation in plan.operations:
        base = python_symbol(operation.operation_id)
        request = _request_symbol(operation)
        lines.append(f"class {request}(BaseModel):")
        lines.append("    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)")
        if not operation.parameters and operation.request_body is None:
            lines.append("    pass")
        for parameter in operation.parameters:
            annotation = emit_annotation(parameter.schema)
            if not parameter.required:
                annotation += " | None"
            default = "" if parameter.required else " = None"
            lines.append(f"    {field_symbol(parameter.name)}: {annotation}{default}")
        if operation.request_body is not None:
            lines.append(f"    body: {emit_annotation(operation.request_body)}")
        lines.append("")
        success = _success_symbol(operation)
        variants = operation.successes
        if len(variants) == 1 and variants[0].schema is not None:
            lines.extend(
                [f"class {success}(RootModel[{emit_annotation(variants[0].schema)}]):", "    pass", ""]
            )
        elif len(variants) == 1 and variants[0].status == 204:
            lines.extend(
                [f"class {success}(BaseModel):", "    status: Literal[204] = 204", ""]
            )
        else:
            raise ValueError(f"{operation.operation_id}: multiple success emission not implemented")
        security = f"{base.upper()}_SECURITY"
        descriptor = f"{base.upper()}_OPERATION"
        lines.extend(
            [
                f"{security} = SecurityMetadata(",
                f"    identity={operation.security_contract_id!r}, public={operation.public!r}, access_required={not operation.public!r},",
                "    signed_request_required=False, human_intent_required=False,",
                f"    source_symbol={operation.operation_id!r}, review_owner='Stage 1B0-R7',",
                ")",
                f"{descriptor} = NormalizedOperation(",
                f"    matrix_id={operation.matrix_id!r}, operation_id={operation.operation_id!r},",
                f"    method={operation.method!r}, path={operation.path!r}, backend_tag={operation.domain!r},",
                f"    product={operation.product!r}, disposition={operation.disposition!r},",
                f"    success_status={variants[0].status}, response_type={success}, security={security},",
                f"    retry_safe=True, owner={operation.owner_module + ':' + operation.callable_name!r},",
                f"    response_media_type={variants[0].media_type!r},",
                ")",
                f"async def {operation.callable_name}(transport: HttpTransport, request: {request}) -> {success}:",
            ]
        )
        path_items = [p for p in operation.parameters if p.location == "path"]
        query_items = [p for p in operation.parameters if p.location == "query"]
        path_expr = "{" + ", ".join(f"{p.name!r}: str(request.{field_symbol(p.name)})" for p in path_items) + "}"
        query_expr = "{" + ", ".join(
            f"{p.name!r}: serialize_query_value(request.{field_symbol(p.name)})"
            for p in query_items
        ) + "}"
        body_expr = "request.body.model_dump(mode='json')" if operation.request_body is not None else "None"
        lines.extend(
            [
                f"    return await transport.invoke({descriptor}, path_parameters={path_expr}, query_parameters={query_expr}, body={body_expr})",
                "",
            ]
        )
        ownership.append(
            f"    {operation.operation_id!r}: ({operation.matrix_id!r}, {operation.owner_module!r}, {operation.callable_name!r}),"
        )
        registry.append(
            f"    ContractRegistryEntry(registry_id={'http:' + operation.operation_id!r}, source_head=SOURCE_HEAD, operation={descriptor}, request_schema={request!r}, success_schema={success!r}),"
        )
    lines.extend([f"SOURCE_HEAD = {plan.source_revision!r}", "", "OWNERSHIP = {"])
    lines.extend(ownership)
    lines.extend(["}", "", "FEATURE_53 = ("])
    lines.extend(registry)
    lines.extend([")", ""])
    return "\n".join(lines)
