"""Market Time Machine analytics service errors."""


class MarketTimeMachineError(RuntimeError):
    """Base Market Time Machine error."""


class MarketTimeMachineQueryBoundsError(MarketTimeMachineError):
    """Raised when query bounds are invalid."""


class MarketTimeMachineProjectionMissingError(MarketTimeMachineError):
    """Raised when a requested ClickHouse projection is not available."""
