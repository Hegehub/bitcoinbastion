from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, str] | None = None


class ApiEnvelopeMeta(BaseModel):
    version: str = "v1"


class ApiEnvelope(BaseModel):
    data: object | None = None
    error: ApiError | None = None
    meta: ApiEnvelopeMeta = ApiEnvelopeMeta()
