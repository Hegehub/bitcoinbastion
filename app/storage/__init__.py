"""Stable public exports for the storage abstraction package."""

from app.storage.interfaces import StorageEngineDescriptor, StorageHealthResult
from app.storage.registry import StorageRegistry, build_default_storage_registry

__all__ = [
    "StorageEngineDescriptor",
    "StorageHealthResult",
    "StorageRegistry",
    "build_default_storage_registry",
]
