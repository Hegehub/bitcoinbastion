from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from bastion_ui.transport.foundation import NormalizedOperation, SafeTransportError


class LifecycleStatus(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    EMPTY = "empty"
    PARTIAL = "partial"
    STALE = "stale"
    DEGRADED = "degraded"
    CONFLICTING = "conflicting"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not-found"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation-error"
    RATE_LIMITED = "rate-limited"
    SERVER_ERROR = "server-error"


@dataclass(frozen=True)
class SafeViewError:
    status: int | None
    code: str
    summary: str
    retryable: bool


def project_transport_error(error: SafeTransportError) -> tuple[LifecycleStatus, SafeViewError]:
    status_map = {
        401: LifecycleStatus.UNAUTHORIZED,
        403: LifecycleStatus.FORBIDDEN,
        404: LifecycleStatus.NOT_FOUND,
        409: LifecycleStatus.CONFLICT,
        422: LifecycleStatus.VALIDATION_ERROR,
        429: LifecycleStatus.RATE_LIMITED,
    }
    status = status_map.get(error.status) if error.status is not None else None
    if status is None:
        status = LifecycleStatus.SERVER_ERROR if error.status else LifecycleStatus.OFFLINE
    return status, SafeViewError(error.status, error.code, error.safe_message, error.retryable)


class LatestRequestWins[T]:
    """Small request identity primitive; only the newest token may commit State."""

    def __init__(self) -> None:
        self._generation = 0

    def begin(self) -> int:
        self._generation += 1
        return self._generation

    def is_current(self, token: int) -> bool:
        return token == self._generation

    def cancel(self) -> None:
        self._generation += 1


async def execute_with_bounded_retry[T](
    operation: NormalizedOperation[BaseModel],
    call: Callable[[], Awaitable[T]],
    *,
    maximum_attempts: int = 2,
) -> T:
    if maximum_attempts < 1:
        raise ValueError("maximum_attempts_must_be_positive")
    allowed_attempts = maximum_attempts if operation.retry_safe and operation.method == "GET" else 1
    last: SafeTransportError | None = None
    for attempt in range(allowed_attempts):
        try:
            return await call()
        except asyncio.CancelledError:
            raise
        except SafeTransportError as error:
            last = error
            if not error.retryable or attempt + 1 == allowed_attempts:
                raise
    assert last is not None
    raise last
