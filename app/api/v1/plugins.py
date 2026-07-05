from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.access_dependencies import require_human_intent, require_plan
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.plugins.errors import PluginRegistryError, PluginSandboxError
from app.plugins.loader import register_builtin_plugins
from app.plugins.manifest import SENSITIVE_TERMS
from app.plugins.registry import RegisteredPlugin, plugin_registry
from app.schemas.base import ResponseEnvelope

router = APIRouter(prefix="/plugins", tags=["plugins"])
register_builtin_plugins()


class PluginDryRunRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


def _scan_forbidden_input(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_scan_forbidden_input(item) for pair in value.items() for item in pair)
    if isinstance(value, (list, tuple, set)):
        return any(_scan_forbidden_input(item) for item in value)
    text = str(value).lower()
    return any(term in text for term in SENSITIVE_TERMS) or any(
        term in text for term in ("wallet file", "12 words", "24 words")
    )


def _plugin_payload(registered: RegisteredPlugin) -> dict[str, Any]:
    manifest = registered.manifest
    return {
        "plugin_id": manifest.plugin_id,
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "plugin_type": manifest.plugin_type.value,
        "permissions": [permission.value for permission in manifest.permissions],
        "capabilities": list(manifest.capabilities),
        "limitations": list(manifest.limitations),
        "safety_flags": manifest.safety_flags,
        "enabled": registered.enabled,
        "enabled_by_default": manifest.enabled_by_default,
        "requires_operator_approval": manifest.requires_operator_approval,
        "supports_dry_run": manifest.supports_dry_run,
    }


@router.get("")
def list_plugins() -> ResponseEnvelope[dict[str, Any]]:
    return ResponseEnvelope(
        data={
            "items": [_plugin_payload(plugin) for plugin in plugin_registry.list_plugins()],
            "limitations": [
                "Plugin API is an in-process foundation; remote plugin loading is not enabled.",
                "Plugins cannot access custody secrets, sign transactions, broadcast transactions, or approve treasury actions.",
            ],
            "safety_flags": {"no_custody": True, "deny_by_default": True, "dry_run_first": True},
        }
    )


@router.get("/{plugin_id}")
def get_plugin(plugin_id: str) -> ResponseEnvelope[dict[str, Any]]:
    try:
        registered = plugin_registry.get_plugin(plugin_id)
    except PluginRegistryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResponseEnvelope(data=_plugin_payload(registered))


@router.post("/{plugin_id}/enable")
def enable_plugin(
    plugin_id: str,
    _access_context: AccessContext = Depends(require_human_intent("enterprise_policy_change")),
) -> ResponseEnvelope[dict[str, Any]]:
    try:
        plugin_registry.enable_plugin(plugin_id)
        registered = plugin_registry.get_plugin(plugin_id)
    except PluginRegistryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResponseEnvelope(data=_plugin_payload(registered))


@router.post("/{plugin_id}/disable")
def disable_plugin(
    plugin_id: str,
    _access_context: AccessContext = Depends(require_human_intent("enterprise_policy_change")),
) -> ResponseEnvelope[dict[str, Any]]:
    try:
        plugin_registry.disable_plugin(plugin_id)
        registered = plugin_registry.get_plugin(plugin_id)
    except PluginRegistryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResponseEnvelope(data=_plugin_payload(registered))


@router.post("/{plugin_id}/dry-run")
def dry_run_plugin(
    plugin_id: str,
    request: PluginDryRunRequest,
    _access_context: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
) -> ResponseEnvelope[dict[str, Any]]:
    if _scan_forbidden_input(request.payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plugin dry-run payload cannot include seed phrases, private keys, wallet files, or signing material.",
        )
    try:
        result = plugin_registry.dry_run_plugin(plugin_id, request.payload)
    except PluginRegistryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PluginSandboxError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ResponseEnvelope(data=result)
