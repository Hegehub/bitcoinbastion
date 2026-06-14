import pytest

from app.plugins.errors import PluginPermissionError
from app.plugins.permissions import (
    PluginPermission,
    admin_permission_is_explicitly_allowed,
    default_allowed_permissions,
    permission_is_allowed,
    validate_permission,
    validate_permissions,
)


def test_known_permissions_accepted() -> None:
    assert validate_permission("read:market") == PluginPermission.READ_MARKET
    assert validate_permissions(["read:market", "read:market"]) == (PluginPermission.READ_MARKET,)


def test_unknown_permissions_rejected() -> None:
    with pytest.raises(PluginPermissionError):
        validate_permission("network:anywhere")


def test_forbidden_permissions_rejected() -> None:
    with pytest.raises(PluginPermissionError):
        validate_permission("wallet:broadcast_transaction")


def test_deny_by_default_behavior_works() -> None:
    assert default_allowed_permissions() == ()
    assert not permission_is_allowed("read:market")


def test_admin_permissions_require_explicit_allow() -> None:
    assert not admin_permission_is_explicitly_allowed("admin:plugin_enable", [])
    assert admin_permission_is_explicitly_allowed(
        "admin:plugin_enable", [PluginPermission.ADMIN_PLUGIN_ENABLE]
    )
