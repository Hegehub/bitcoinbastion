import pytest
from pydantic import ValidationError

from app.plugins.base import BasePlugin, PluginType
from app.plugins.errors import PluginManifestError, PluginRegistryError
from app.plugins.manifest import PluginManifest
from app.plugins.permissions import PluginPermission
from app.plugins.registry import PluginRegistry


class DummyPlugin(BasePlugin):
    pass


def valid_manifest(**overrides: object) -> PluginManifest:
    data = {
        "plugin_id": "example.provider",
        "name": "Example Provider",
        "version": "0.1.0",
        "description": "Read-only provider plugin for tests.",
        "plugin_type": PluginType.PROVIDER,
        "entrypoint": "tests.plugins:ExampleProvider",
        "permissions": [PluginPermission.READ_MARKET],
        "capabilities": ["health_check"],
        "limitations": ["Read-only plugin test fixture."],
        "safety_flags": {"no_custody": True, "no_signing": True},
    }
    data.update(overrides)
    return PluginManifest(**data)


def test_valid_manifest_accepted() -> None:
    manifest = valid_manifest()

    assert manifest.plugin_id == "example.provider"
    assert manifest.plugin_type == PluginType.PROVIDER
    assert manifest.permissions == (PluginPermission.READ_MARKET,)


def test_missing_required_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        PluginManifest(plugin_id="missing.fields")  # type: ignore[call-arg]


def test_invalid_plugin_type_rejected() -> None:
    with pytest.raises(ValidationError):
        valid_manifest(plugin_type="wallet")


def test_duplicate_plugin_id_rejected() -> None:
    registry = PluginRegistry()
    plugin = DummyPlugin(valid_manifest())
    registry.register_plugin(plugin)

    with pytest.raises(PluginRegistryError):
        registry.register_plugin(DummyPlugin(valid_manifest()))


def test_forbidden_custody_permission_rejected() -> None:
    with pytest.raises(ValidationError):
        valid_manifest(permissions=["custody:seed"])


def test_forbidden_signing_permission_rejected() -> None:
    with pytest.raises(ValidationError):
        valid_manifest(permissions=["wallet:sign_transaction"])


def test_sensitive_manifest_text_rejected() -> None:
    with pytest.raises(PluginManifestError):
        valid_manifest(description="requests private key material")
