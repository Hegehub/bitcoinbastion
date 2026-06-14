from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from app.plugins.base import BasePlugin, PluginType
from app.plugins.errors import PluginRegistryError, PluginSandboxError
from app.plugins.manifest import PluginManifest
from app.plugins.sandbox import PluginSandboxPolicy

PLUGIN_EVENT_TYPES: tuple[str, ...] = (
    "plugin.registered",
    "plugin.enabled",
    "plugin.disabled",
    "plugin.validation_failed",
    "plugin.permission_denied",
    "plugin.execution_blocked",
    "plugin.dry_run_completed",
    "plugin.event_emitted",
)


@dataclass(frozen=True)
class PluginAuditRecord:
    event_type: str
    plugin_id: str
    occurred_at: datetime
    details: dict[str, Any]


@dataclass
class RegisteredPlugin:
    plugin: BasePlugin
    manifest: PluginManifest
    sandbox_policy: PluginSandboxPolicy
    enabled: bool = False


AuditHook = Callable[[PluginAuditRecord], None]


class PluginRegistry:
    def __init__(self, audit_hook: AuditHook | None = None) -> None:
        self._plugins: dict[str, RegisteredPlugin] = {}
        self._audit_records: list[PluginAuditRecord] = []
        self._audit_hook = audit_hook

    @property
    def audit_records(self) -> tuple[PluginAuditRecord, ...]:
        return tuple(self._audit_records)

    def register_plugin(
        self,
        plugin: BasePlugin,
        sandbox_policy: PluginSandboxPolicy | None = None,
        *,
        safe_builtin: bool = False,
    ) -> None:
        manifest = plugin.manifest
        if manifest.plugin_id in self._plugins:
            self._audit("plugin.validation_failed", manifest.plugin_id, {"reason": "duplicate_plugin_id"})
            raise PluginRegistryError(f"Plugin already registered: {manifest.plugin_id}")
        policy = sandbox_policy or PluginSandboxPolicy.default()
        enabled = bool(safe_builtin and manifest.enabled_by_default)
        self._plugins[manifest.plugin_id] = RegisteredPlugin(
            plugin=plugin,
            manifest=manifest,
            sandbox_policy=policy,
            enabled=enabled,
        )
        self._audit("plugin.registered", manifest.plugin_id, {"plugin_type": manifest.plugin_type.value})
        if enabled:
            self._audit("plugin.enabled", manifest.plugin_id, {"safe_builtin": True})

    def unregister_plugin(self, plugin_id: str) -> None:
        self._plugins.pop(plugin_id, None)

    def get_plugin(self, plugin_id: str) -> RegisteredPlugin:
        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            raise PluginRegistryError(f"Plugin not found: {plugin_id}") from exc

    def list_plugins(self) -> list[RegisteredPlugin]:
        return list(self._plugins.values())

    def list_plugins_by_type(self, plugin_type: PluginType) -> list[RegisteredPlugin]:
        return [item for item in self._plugins.values() if item.manifest.plugin_type == plugin_type]

    def is_plugin_enabled(self, plugin_id: str) -> bool:
        return self.get_plugin(plugin_id).enabled

    def enable_plugin(self, plugin_id: str) -> None:
        registered = self.get_plugin(plugin_id)
        registered.enabled = True
        self._audit("plugin.enabled", plugin_id, {"operator_approval_required": True})

    def disable_plugin(self, plugin_id: str) -> None:
        registered = self.get_plugin(plugin_id)
        if registered.enabled:
            registered.enabled = False
        self._audit("plugin.disabled", plugin_id, {})

    def dry_run_plugin(self, plugin_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        registered = self.get_plugin(plugin_id)
        if not registered.enabled:
            self._audit("plugin.execution_blocked", plugin_id, {"reason": "plugin_disabled"})
            raise PluginSandboxError("Disabled plugins cannot execute, including dry-run execution")
        registered.sandbox_policy.assert_can_execute(payload=payload or {}, dry_run=True)
        result = registered.plugin.dry_run(payload or {})
        self._audit("plugin.dry_run_completed", plugin_id, {"dry_run": True})
        return result

    def _audit(self, event_type: str, plugin_id: str, details: dict[str, Any]) -> None:
        record = PluginAuditRecord(
            event_type=event_type,
            plugin_id=plugin_id,
            occurred_at=datetime.now(UTC),
            details=details,
        )
        self._audit_records.append(record)
        if self._audit_hook is not None:
            self._audit_hook(record)


plugin_registry = PluginRegistry()
