from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class LNURLSuccessMessage:
    message: str


@dataclass(frozen=True, slots=True)
class LNURLSuccessURL:
    description: str
    url: str

    def __post_init__(self) -> None:
        parsed = urlsplit(self.url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("successAction URL must be an HTTPS URL without credentials")
