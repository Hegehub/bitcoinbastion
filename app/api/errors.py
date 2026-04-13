from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.error import ErrorEnvelope, ErrorPayload


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorPayload(code=exc.code, message=exc.message, request_id=_request_id(request))
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorPayload(code="validation_error", message=str(exc), request_id=_request_id(request))
        )
        return JSONResponse(status_code=422, content=envelope.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        envelope = ErrorEnvelope(
            error=ErrorPayload(code="http_error", message=str(exc.detail), request_id=_request_id(request))
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())
