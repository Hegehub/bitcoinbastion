"""TimescaleDB storage-layer errors.

Errors in this module are intentionally safe to log and must not include DSNs,
passwords, access tokens, or other secrets.
"""

from app.storage.errors import StorageConfigurationError, StorageError, StorageHealthError


class TimescaleError(StorageError):
    """Base error for TimescaleDB foundation failures."""


class TimescaleConfigurationError(StorageConfigurationError, TimescaleError):
    """Raised when TimescaleDB configuration or identifiers are invalid."""


class TimescaleHypertableError(TimescaleError):
    """Raised when a TimescaleDB helper cannot prepare a hypertable safely."""


class TimescaleHealthError(StorageHealthError, TimescaleError):
    """Raised when TimescaleDB health checks fail unexpectedly."""
