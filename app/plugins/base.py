from __future__ import annotations

from abc import ABC
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.plugins.manifest import PluginManifest


class PluginType(StrEnum):
    PROVIDER = "provider"
    SCORING_RULE = "scoring_rule"
    DELIVERY_CHANNEL = "delivery_channel"
    DASHBOARD_MODULE = "dashboard_module"
    TREASURY_CHECK = "treasury_check"
    POLICY_RULE = "policy_rule"


class BasePlugin(ABC):
    """Narrow base contract for in-process Bitcoin Bastion plugins."""

    manifest: "PluginManifest"

    def __init__(self, manifest: "PluginManifest") -> None:
        self.manifest = manifest

    @property
    def plugin_id(self) -> str:
        return self.manifest.plugin_id

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version

    @property
    def description(self) -> str:
        return self.manifest.description

    @property
    def plugin_type(self) -> PluginType:
        return self.manifest.plugin_type

    @property
    def permissions(self) -> tuple[str, ...]:
        return tuple(permission.value for permission in self.manifest.permissions)

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self.manifest.capabilities

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.manifest.limitations

    @property
    def enabled_by_default(self) -> bool:
        return self.manifest.enabled_by_default

    def dry_run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "dry_run": True,
            "payload_received": bool(payload),
            "limitations": list(self.limitations),
            "safety_flags": self.manifest.safety_flags,
        }
