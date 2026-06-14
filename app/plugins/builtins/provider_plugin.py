from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin


class ProviderPlugin(BasePlugin):
    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return provider health metadata without exposing secrets."""

    @abstractmethod
    def describe_source(self) -> dict[str, Any]:
        """Describe source provenance and limitations."""

    @abstractmethod
    def fetch_sample(self) -> dict[str, Any]:
        """Fetch a bounded, non-secret sample for validation."""
