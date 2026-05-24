import time
import uuid
from collections import defaultdict
from typing import cast

from redis import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.core.request_limits import MAX_BATCH_BODY_BYTES, MAX_REQUEST_BODY_BYTES
from app.core.security import CSP_POLICY, SECURITY_HEADERS
from app.schemas.error import ErrorEnvelope, ErrorPayload


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cl = request.headers.get('content-length')
        if cl and cl.isdigit():
            max_size = MAX_BATCH_BODY_BYTES if '/trace/business/batch' in request.url.path else MAX_REQUEST_BODY_BYTES
            if int(cl) > max_size:
                envelope = ErrorEnvelope(error=ErrorPayload(code='validation_error', message='Request payload too large', request_id=getattr(request.state, 'request_id', None)))
                return JSONResponse(status_code=413, content=envelope.model_dump())
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers[k] = v
        response.headers['Content-Security-Policy'] = CSP_POLICY
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    _fallback_buckets: dict[str, int] = defaultdict(int)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        now_min = int(time.time() // 60)
        path = request.url.path
        client_ip = request.client.host if request.client else 'unknown'
        key = f'rate:{client_ip}:{path}:{now_min}'

        limited = False
        try:
            redis_client = get_redis_client()
            value = cast(int, redis_client.incr(key))
            if value == 1:
                redis_client.expire(key, 70)
            limit = settings.rate_limit_per_minute // 2 if path.startswith('/api/v1/public') else settings.rate_limit_per_minute
            limited = value > limit
        except RedisError:
            self._fallback_buckets[key] += 1
            limited = self._fallback_buckets[key] > settings.rate_limit_per_minute

        if limited:
            envelope = ErrorEnvelope(error=ErrorPayload(code='rate_limited', message='Rate limit exceeded', request_id=getattr(request.state, 'request_id', None)))
            return JSONResponse(status_code=429, content=envelope.model_dump())

        return await call_next(request)
