from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin


class TreasuryPlugin(BasePlugin):
    @abstractmethod
    def describe_check(self) -> dict[str, Any]:
        """Describe a draft-only treasury check."""

    @abstractmethod
    def evaluate_draft(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a draft; never approve, sign, broadcast, or move funds."""
