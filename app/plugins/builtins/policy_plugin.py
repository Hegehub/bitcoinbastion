from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin


class PolicyPlugin(BasePlugin):
    @abstractmethod
    def describe_policy_rule(self) -> dict[str, Any]:
        """Describe an operator-controlled policy rule."""

    @abstractmethod
    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate policy without executing the proposed action."""
