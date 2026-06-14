import pytest

from app.plugins.errors import PluginSandboxError
from app.plugins.permissions import PluginPermission
from app.plugins.sandbox import PluginSandboxPolicy


def test_default_sandbox_denies_network_filesystem_and_secret_access() -> None:
    policy = PluginSandboxPolicy.default()

    with pytest.raises(PluginSandboxError):
        policy.assert_no_network_access()
    with pytest.raises(PluginSandboxError):
        policy.assert_no_filesystem_access()
    with pytest.raises(PluginSandboxError):
        policy.assert_no_secret_access()


def test_default_sandbox_requires_dry_run() -> None:
    policy = PluginSandboxPolicy.default()

    with pytest.raises(PluginSandboxError):
        policy.assert_can_execute(dry_run=False)


def test_permission_denied_blocks_execution() -> None:
    policy = PluginSandboxPolicy.default()

    with pytest.raises(PluginSandboxError):
        policy.check_permission(PluginPermission.READ_MARKET)


def test_allowed_permission_can_pass_when_explicit() -> None:
    policy = PluginSandboxPolicy(allowed_permissions=[PluginPermission.READ_MARKET])

    assert policy.check_permission("read:market") == PluginPermission.READ_MARKET


def test_payload_limit_enforced() -> None:
    policy = PluginSandboxPolicy(payload_size_limits=1024)

    with pytest.raises(PluginSandboxError):
        policy.validate_payload_size({"x": "a" * 2048})
