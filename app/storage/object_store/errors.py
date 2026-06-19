"""Typed, log-safe Object Storage errors."""

from app.storage.errors import StorageSafetyError, StorageUnavailableError


class ObjectStoreError(Exception):
    """Base Object Storage error. Messages must be safe to log."""


class ObjectStoreConfigurationError(ObjectStoreError):
    """Raised when Object Storage configuration is invalid."""


class ObjectStoreUnavailableError(ObjectStoreError, StorageUnavailableError):
    """Raised when an Object Storage backend is unavailable."""


class ObjectStoreNotFoundError(ObjectStoreError):
    """Raised when an object is not found."""


class ObjectStoreChecksumError(ObjectStoreError):
    """Raised when an object checksum is missing or mismatched."""


class ObjectStoreSecurityError(ObjectStoreError, StorageSafetyError):
    """Raised when object keys or metadata violate storage safety rules."""


class ObjectStoreSizeError(ObjectStoreError):
    """Raised when an object exceeds configured size limits."""
