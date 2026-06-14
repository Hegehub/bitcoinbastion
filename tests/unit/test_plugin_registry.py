import pytest

from app.plugins.base import BasePlugin, PluginType
from app.plugins.errors import PluginRegistryError, PluginSandboxError
from app.plugins.manifest import PluginManifest
from app.plugins.permissions import PluginPermission
from app.plugins.registry import PluginRegistry
from app.plugins.sandbox import PluginSandboxPolicy


class DummyPlugin(BasePlugin):
    pass


def make_plugin(plugin_id: str = "test.plugin", plugin_type: PluginType = PluginType.PROVIDER) -> DummyPlugin:
    return DummyPlugin(
        PluginManifest(
            plugin_id=plugin_id,
            name="Test Plugin",
            version="0.1.0",
            description="Read-only plugin fixture.",
            plugin_type=plugin_type,
            entrypoint="tests.plugins:TestPlugin",
            permissions=[PluginPermission.READ_PROVIDER_HEALTH],
            capabilities=["dry_run"],
            limitations=["Test fixture only."],
            enabled_by_default=True,
        )
    )


def test_register_list_get_and_list_by_type() -> None:
    registry = PluginRegistry()
    plugin = make_plugin()

    registry.register_plugin(plugin)

    assert registry.get_plugin("test.plugin").plugin is plugin
    assert len(registry.list_plugins()) == 1
    assert len(registry.list_plugins_by_type(PluginType.PROVIDER)) == 1


def test_disable_plugin_is_idempotent_and_enable_plugin_works() -> None:
    registry = PluginRegistry()
    registry.register_plugin(make_plugin(), safe_builtin=True)

    assert registry.is_plugin_enabled("test.plugin")
    registry.disable_plugin("test.plugin")
    registry.disable_plugin("test.plugin")
    assert not registry.is_plugin_enabled("test.plugin")
    registry.enable_plugin("test.plugin")
    assert registry.is_plugin_enabled("test.plugin")


def test_duplicate_plugin_rejected() -> None:
    registry = PluginRegistry()
    registry.register_plugin(make_plugin())

    with pytest.raises(PluginRegistryError):
        registry.register_plugin(make_plugin())


def test_disabled_plugin_cannot_execute() -> None:
    registry = PluginRegistry()
    registry.register_plugin(make_plugin())

    with pytest.raises(PluginSandboxError):
        registry.dry_run_plugin("test.plugin", {"ok": True})


def test_enabled_plugin_can_dry_run_with_bounded_policy() -> None:
    registry = PluginRegistry()
    plugin = make_plugin()
    registry.register_plugin(
        plugin,
        sandbox_policy=PluginSandboxPolicy(allowed_permissions=plugin.manifest.permissions),
        safe_builtin=True,
    )

    result = registry.dry_run_plugin("test.plugin", {"ok": True})

    assert result["dry_run"] is True
    assert any(record.event_type == "plugin.dry_run_completed" for record in registry.audit_records)
