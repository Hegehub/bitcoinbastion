import time
import uuid
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.schemas.error import ErrorEnvelope, ErrorPayload


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    _buckets: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        settings = get_settings()
        now_min = int(time.time() // 60)
        key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}:{now_min}"

        count, _ = self._buckets[key]
        if count >= settings.rate_limit_per_minute:
            envelope = ErrorEnvelope(
                error=ErrorPayload(
                    code="rate_limited",
                    message="Rate limit exceeded",
                    request_id=getattr(request.state, "request_id", None),
                )
            )
            return JSONResponse(status_code=429, content=envelope.model_dump())

        self._buckets[key] = (count + 1, now_min)
        return await call_next(request)
