from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: T


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
