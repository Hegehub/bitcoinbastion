from app.storage.errors import StorageProjectionError, StorageSafetyError


class StorageOutboxError(Exception):
    """Base storage outbox error. Messages must be safe to log."""


class StorageOutboxValidationError(StorageOutboxError, StorageSafetyError):
    """Raised when storage outbox event input is invalid or unsafe."""


class StorageOutboxRepositoryError(StorageOutboxError):
    """Raised when storage outbox persistence fails."""


class StorageOutboxProjectionError(StorageOutboxError, StorageProjectionError):
    """Raised by future projection workers when projection fails."""
