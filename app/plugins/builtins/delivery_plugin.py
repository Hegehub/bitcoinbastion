from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.plugins.base import BasePlugin
from app.plugins.errors import PluginSandboxError


class DeliveryPlugin(BasePlugin):
    @abstractmethod
    def describe_channel(self) -> dict[str, Any]:
        """Describe an operator-approved delivery channel."""

    def dry_run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "channel": self.describe_channel(),
            "dry_run": True,
            "payload_received": bool(payload),
            "limitations": list(self.limitations),
            "safety_flags": self.manifest.safety_flags,
        }

    def deliver(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise PluginSandboxError(
            "Delivery plugins cannot dispatch directly without sandbox approval"
        )
