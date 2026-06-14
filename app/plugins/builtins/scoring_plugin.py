from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin


class ScoringPlugin(BasePlugin):
    @abstractmethod
    def describe_rule(self) -> dict[str, Any]:
        """Describe an evidence-based scoring rule."""

    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate context without making legal, custody, or market guarantees."""
