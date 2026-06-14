import pytest

from app.plugins.errors import PluginPermissionError
from app.plugins.permissions import FORBIDDEN_PERMISSIONS, default_allowed_permissions, validate_permission
from app.plugins.sandbox import PluginSandboxPolicy


def test_forbidden_plugin_permissions_are_rejected() -> None:
    for permission in FORBIDDEN_PERMISSIONS:
        with pytest.raises(PluginPermissionError):
            validate_permission(permission)


def test_plugin_sandbox_is_least_privilege_by_default() -> None:
    assert default_allowed_permissions() == ()
    policy = PluginSandboxPolicy.default()
    assert policy.allowed_permissions == ()
    assert not policy.network_access
    assert not policy.filesystem_access
    assert not policy.secret_access
    assert policy.dry_run_required
