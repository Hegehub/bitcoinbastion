from typing import Any

from app.storage.outbox.enums import StorageOutboxEventStatus, StorageOutboxTargetStore
from app.storage.outbox.schemas import (
    StorageOutboxEventClaim,
    StorageOutboxEventCreate,
    StorageOutboxEventRead,
    StorageOutboxEventResult,
)

__all__ = [
    "StorageOutboxEventClaim",
    "StorageOutboxEventCreate",
    "StorageOutboxEventRead",
    "StorageOutboxEventResult",
    "StorageOutboxEventStatus",
    "StorageOutboxService",
    "StorageOutboxTargetStore",
]


def __getattr__(name: str) -> Any:
    if name == "StorageOutboxService":
        from app.storage.outbox.service import StorageOutboxService

        return StorageOutboxService
    raise AttributeError(name)
