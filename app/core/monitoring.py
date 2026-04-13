from dataclasses import dataclass


@dataclass
class ErrorEvent:
    source: str
    message: str
    context: dict[str, str] | None = None


class ErrorReporter:
    def capture(self, event: ErrorEvent) -> None:
        # Sentry-compatible adapter point.
        return None
