from pydantic import BaseModel


class ErrorPayload(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorPayload
