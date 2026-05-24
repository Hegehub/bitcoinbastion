from app.schemas.api_contracts import ApiEnvelope, ApiEnvelopeMeta, ApiError


def ok(data: object, *, version: str = 'v1') -> ApiEnvelope:
    return ApiEnvelope(data=data, error=None, meta=ApiEnvelopeMeta(version=version))


def fail(code: str, message: str, *, details: dict[str, str] | None = None, version: str = 'v1') -> ApiEnvelope:
    return ApiEnvelope(data=None, error=ApiError(code=code, message=message, details=details), meta=ApiEnvelopeMeta(version=version))
