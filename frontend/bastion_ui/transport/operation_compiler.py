"""Normalize OpenAPI operations once for deterministic source emission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema_compiler import CompiledSchema, OpenAPISchemaCompiler, SchemaCompileError


@dataclass(frozen=True)
class CompiledParameter:
    name: str
    location: str
    required: bool
    schema: CompiledSchema


@dataclass(frozen=True)
class CompiledResponse:
    status: int
    media_type: str
    schema: CompiledSchema | None


@dataclass(frozen=True)
class CompiledOperation:
    matrix_id: str
    operation_id: str
    method: str
    path: str
    product: str
    domain: str
    disposition: str
    authority: str
    parameters: tuple[CompiledParameter, ...]
    request_body: CompiledSchema | None
    request_media_type: str | None
    successes: tuple[CompiledResponse, ...]
    errors: tuple[CompiledResponse, ...]
    security_contract_id: str
    public: bool
    mutation_contract_id: str | None
    owner_module: str
    callable_name: str

    def validate_complete(self) -> None:
        required = {
            "matrix_id": self.matrix_id,
            "operation_id": self.operation_id,
            "method": self.method,
            "path": self.path,
            "product": self.product,
            "domain": self.domain,
            "disposition": self.disposition,
            "authority": self.authority,
            "security_contract_id": self.security_contract_id,
            "owner_module": self.owner_module,
            "callable_name": self.callable_name,
        }
        for field, value in required.items():
            if not value:
                raise SchemaCompileError(
                    f"{self.matrix_id}/{self.operation_id}: missing CompiledOperation.{field}"
                )
        if not self.successes:
            raise SchemaCompileError(
                f"{self.matrix_id}/{self.operation_id}: missing CompiledOperation.successes"
            )


def compile_operations(
    spec: dict[str, Any], matrix_rows: list[dict[str, Any]]
) -> tuple[CompiledOperation, ...]:
    components = spec["components"]["schemas"]
    compiler = OpenAPISchemaCompiler(components)
    paths = spec["paths"]
    result: list[CompiledOperation] = []
    for row in sorted(matrix_rows, key=lambda item: str(item["matrix_id"])):
        method = str(row["method"]).lower()
        raw = paths[str(row["path"])][method]
        raw_parameters = raw.get("parameters", [])
        security_headers = {
            str(parameter["name"]).lower()
            for parameter in raw_parameters
            if parameter.get("in") == "header"
            and str(parameter["name"]).lower().startswith("x-bastion-")
        }
        access_required = bool(raw.get("security")) or "x-bastion-session" in security_headers
        parameters = tuple(
            CompiledParameter(
                str(parameter["name"]),
                str(parameter["in"]),
                bool(parameter.get("required", False)),
                compiler.compile(
                    parameter["schema"],
                    location=f"paths.{row['path']}.{method}.parameters.{parameter['name']}",
                ),
            )
            for parameter in raw_parameters
            if str(parameter["name"]).lower() not in security_headers
        )
        request_body = raw.get("requestBody")
        body_schema = None
        body_media = None
        if request_body:
            body_media = sorted(request_body["content"])[0]
            body_schema = compiler.compile(
                request_body["content"][body_media]["schema"],
                location=f"paths.{row['path']}.{method}.requestBody",
            )
        successes: list[CompiledResponse] = []
        errors: list[CompiledResponse] = []
        for status, response in sorted(raw.get("responses", {}).items()):
            if not str(status).isdigit():
                continue
            content = response.get("content", {})
            media = sorted(content)[0] if content else "none"
            schema = (
                compiler.compile(
                    content[media]["schema"],
                    location=f"paths.{row['path']}.{method}.responses.{status}",
                )
                if content
                else None
            )
            target = successes if 200 <= int(status) < 300 else errors
            target.append(CompiledResponse(int(status), media, schema))
        operation = CompiledOperation(
            matrix_id=str(row["matrix_id"]),
            operation_id=str(row["operation_id"]),
            method=str(row["method"]),
            path=str(row["path"]),
            product=str(row["product_boundary"]),
            domain=str(row["backend_owner"]),
            disposition=str(row["disposition"]),
            authority=str(row["authority_status"]),
            parameters=parameters,
            request_body=body_schema,
            request_media_type=body_media,
            successes=tuple(successes),
            errors=tuple(errors),
            security_contract_id=(
                f"access-session:{row['operation_id']}"
                if access_required
                else f"public:{row['operation_id']}"
            ),
            public=not access_required,
            mutation_contract_id=None,
            owner_module="bastion_ui.transport.generated_http",
            callable_name=str(row["operation_id"]),
        )
        operation.validate_complete()
        result.append(operation)
    return tuple(result)
