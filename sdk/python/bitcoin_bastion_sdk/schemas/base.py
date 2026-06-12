from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0
