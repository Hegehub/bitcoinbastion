"""Domain errors for the analytics-store abstraction."""


class AnalyticsStoreError(RuntimeError):
    """Base analytics-store error with sanitized messages."""


class AnalyticsStoreDisabledError(AnalyticsStoreError):
    """Raised when ClickHouse analytics operations are requested while disabled."""


class AnalyticsStoreConfigurationError(AnalyticsStoreError):
    """Raised when analytics-store configuration is invalid."""


class AnalyticsStoreQueryError(AnalyticsStoreError):
    """Raised when an analytics query fails."""


class AnalyticsStoreInsertError(AnalyticsStoreError):
    """Raised when an analytics insert fails."""
