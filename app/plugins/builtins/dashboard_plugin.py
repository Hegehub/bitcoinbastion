from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin


class DashboardPlugin(BasePlugin):
    @abstractmethod
    def describe_panel(self) -> dict[str, Any]:
        """Describe a dashboard panel and its limitations."""

    @abstractmethod
    def get_panel_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return bounded dashboard data without hidden automation."""
