from __future__ import annotations

from typing import Any

from app.plugins.base import BasePlugin, PluginType
from app.plugins.manifest import PluginManifest
from app.plugins.permissions import PluginPermission
from app.plugins.registry import PluginRegistry, plugin_registry
from app.plugins.sandbox import PluginSandboxPolicy


class BuiltinDashboardStatusPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(
            PluginManifest(
                plugin_id="builtin.dashboard.status",
                name="Built-in Status Dashboard Panel",
                version="0.1.0",
                description="Read-only dashboard module for plugin API smoke checks.",
                plugin_type=PluginType.DASHBOARD_MODULE,
                entrypoint="app.plugins.loader:BuiltinDashboardStatusPlugin",
                permissions=(PluginPermission.READ_PROVIDER_HEALTH,),
                capabilities=("dashboard_status_panel", "dry_run"),
                limitations=(
                    "Built-in plugin returns bounded status metadata only.",
                    "Plugins cannot access secrets, sign transactions, or approve treasury actions.",
                ),
                enabled_by_default=True,
                requires_operator_approval=True,
                supports_dry_run=True,
            )
        )

    def dry_run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "dry_run": True,
            "status": "ok",
            "payload_received": bool(payload),
            "limitations": list(self.limitations),
            "safety_flags": self.manifest.safety_flags,
        }


def load_manifest(manifest_data: dict[str, Any]) -> PluginManifest:
    """Validate plugin metadata without importing or executing plugin entrypoint code."""

    return PluginManifest.model_validate(manifest_data)


def builtin_plugins() -> tuple[BasePlugin, ...]:
    return (BuiltinDashboardStatusPlugin(),)


def register_builtin_plugins(registry: PluginRegistry = plugin_registry) -> None:
    for plugin in builtin_plugins():
        if any(item.manifest.plugin_id == plugin.plugin_id for item in registry.list_plugins()):
            continue
        policy = PluginSandboxPolicy(
            allowed_permissions=plugin.manifest.permissions,
            requires_operator_approval=True,
            dry_run_required=True,
        )
        registry.register_plugin(plugin, sandbox_policy=policy, safe_builtin=True)
