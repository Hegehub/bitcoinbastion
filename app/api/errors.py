from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.error import ErrorEnvelope, ErrorPayload


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _map_http_code(detail: str) -> str:
    d = detail.lower()
    if "sensitive wallet material" in d:
        return "sensitive_wallet_material_not_accepted"
    if "invalid" in d and "address" in d:
        return "invalid_bitcoin_address"
    if "not found" in d:
        return "report_not_found"
    return "http_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorPayload(code=exc.code, message=exc.message, request_id=_request_id(request))
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorPayload(
                code="validation_error",
                message="Validation error.",
                request_id=_request_id(request),
            )
        )
        return JSONResponse(status_code=422, content=envelope.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = str(exc.detail)
        envelope = ErrorEnvelope(
            error=ErrorPayload(
                code=_map_http_code(detail), message=detail, request_id=_request_id(request)
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())
