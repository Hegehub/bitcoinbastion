from app.plugins.base import BasePlugin, PluginType
from app.plugins.loader import load_manifest, register_builtin_plugins
from app.plugins.registry import PluginRegistry


class ExplodingPlugin(BasePlugin):
    executed = False

    def __init__(self) -> None:
        ExplodingPlugin.executed = True
        raise AssertionError("plugin code should not execute during manifest inspection")


def test_load_manifest_does_not_execute_entrypoint() -> None:
    manifest = load_manifest(
        {
            "plugin_id": "safe.manifest",
            "name": "Safe Manifest",
            "version": "0.1.0",
            "description": "Manifest-only fixture.",
            "plugin_type": "provider",
            "entrypoint": "tests.unit.test_plugin_loader:ExplodingPlugin",
            "permissions": ["read:market"],
            "capabilities": ["inspect"],
            "limitations": ["Manifest inspection only."],
        }
    )

    assert manifest.plugin_type == PluginType.PROVIDER
    assert not ExplodingPlugin.executed


def test_register_builtin_plugins_registers_safe_builtin() -> None:
    registry = PluginRegistry()

    register_builtin_plugins(registry)

    assert registry.list_plugins()
    assert registry.is_plugin_enabled("builtin.dashboard.status")
