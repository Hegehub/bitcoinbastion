from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from app.plugins.errors import PluginPermissionError


class PluginPermission(StrEnum):
    READ_MARKET = "read:market"
    READ_SIGNALS = "read:signals"
    READ_TRACE = "read:trace"
    READ_EVIDENCE = "read:evidence"
    READ_ONCHAIN = "read:onchain"
    READ_WALLET_HEALTH = "read:wallet_health"
    READ_PROVIDER_HEALTH = "read:provider_health"
    READ_POLICY = "read:policy"
    READ_TREASURY = "read:treasury"

    WRITE_EVIDENCE_ANNOTATION = "write:evidence_annotation"
    WRITE_DELIVERY_EVENT = "write:delivery_event"
    WRITE_OPERATOR_NOTE = "write:operator_note"

    EMIT_EVENT = "emit:event"
    EMIT_WEBHOOK = "emit:webhook"
    EMIT_WEBSOCKET = "emit:websocket"

    PROPOSE_TREASURY_ACTION = "propose:treasury_action"
    PROPOSE_POLICY_ACTION = "propose:policy_action"
    PROPOSE_TRACE_REVIEW = "propose:trace_review"

    ADMIN_PLUGIN_ENABLE = "admin:plugin_enable"
    ADMIN_PLUGIN_DISABLE = "admin:plugin_disable"
    ADMIN_PLUGIN_CONFIGURE = "admin:plugin_configure"


FORBIDDEN_PERMISSIONS: frozenset[str] = frozenset(
    {
        "custody:seed",
        "custody:private_key",
        "custody:wallet_file",
        "custody:signing_material",
        "wallet:sign_transaction",
        "wallet:broadcast_transaction",
        "wallet:derive_key",
        "wallet:export_secret",
    }
)

ADMIN_PERMISSIONS: frozenset[PluginPermission] = frozenset(
    {
        PluginPermission.ADMIN_PLUGIN_ENABLE,
        PluginPermission.ADMIN_PLUGIN_DISABLE,
        PluginPermission.ADMIN_PLUGIN_CONFIGURE,
    }
)


def validate_permission(permission: str | PluginPermission) -> PluginPermission:
    value = str(permission)
    if value in FORBIDDEN_PERMISSIONS:
        raise PluginPermissionError(f"Forbidden plugin permission requested: {value}")
    try:
        return PluginPermission(value)
    except ValueError as exc:
        raise PluginPermissionError(f"Unknown plugin permission requested: {value}") from exc


def validate_permissions(
    permissions: Iterable[str | PluginPermission],
) -> tuple[PluginPermission, ...]:
    seen: set[PluginPermission] = set()
    validated: list[PluginPermission] = []
    for permission in permissions:
        item = validate_permission(permission)
        if item not in seen:
            seen.add(item)
            validated.append(item)
    return tuple(validated)


def default_allowed_permissions() -> tuple[PluginPermission, ...]:
    """Return deny-by-default permission baseline."""

    return ()


def permission_is_allowed(
    permission: str | PluginPermission,
    allowed_permissions: Iterable[str | PluginPermission] | None = None,
) -> bool:
    checked = validate_permission(permission)
    allowed = validate_permissions(allowed_permissions or default_allowed_permissions())
    return checked in allowed


def admin_permission_is_explicitly_allowed(
    permission: str | PluginPermission,
    allowed_permissions: Iterable[str | PluginPermission],
) -> bool:
    checked = validate_permission(permission)
    if checked not in ADMIN_PERMISSIONS:
        return True
    return checked in validate_permissions(allowed_permissions)
