"""Safe exception types for storage scaffolding.

Exception messages in this module must remain safe to log. Do not include DSNs,
credentials, access tokens, object keys containing private context, or secret
material in error messages.
"""


class StorageError(Exception):
    """Base class for storage-layer errors that are safe to log."""


class StorageConfigurationError(StorageError):
    """Raised when storage configuration or profile input is invalid."""


class StorageUnavailableError(StorageError):
    """Raised when a configured storage engine is unavailable."""


class StorageHealthError(StorageError):
    """Raised when a storage health check cannot be evaluated safely."""


class StorageProjectionError(StorageError):
    """Raised when a projection into a derived storage engine fails."""


class StorageSafetyError(StorageError):
    """Raised when storage safety boundaries are violated."""


class UnsupportedStorageEngineError(StorageError):
    """Raised when code references an unknown storage engine."""
