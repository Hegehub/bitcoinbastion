from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.plugins.errors import PluginSandboxError
from app.plugins.permissions import (
    FORBIDDEN_PERMISSIONS,
    PluginPermission,
    validate_permission,
    validate_permissions,
)


class PluginSandboxPolicy(BaseModel):
    allowed_permissions: tuple[PluginPermission, ...] = ()
    denied_permissions: tuple[str, ...] = tuple(sorted(FORBIDDEN_PERMISSIONS))
    network_access: bool = False
    filesystem_access: bool = False
    secret_access: bool = False
    event_emit_limits: int = Field(default=10, ge=0, le=100)
    payload_size_limits: int = Field(default=64_000, ge=1024, le=1_000_000)
    requires_operator_approval: bool = True
    dry_run_required: bool = True

    @field_validator("allowed_permissions", mode="before")
    @classmethod
    def validate_allowed_permissions(cls, value: object) -> tuple[PluginPermission, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("allowed_permissions must be a list")
        return validate_permissions(value)

    @classmethod
    def default(cls) -> "PluginSandboxPolicy":
        return cls()

    def assert_no_network_access(self) -> None:
        if not self.network_access:
            raise PluginSandboxError("Plugin sandbox denies network access by default")

    def assert_no_filesystem_access(self) -> None:
        if not self.filesystem_access:
            raise PluginSandboxError("Plugin sandbox denies filesystem access by default")

    def assert_no_secret_access(self) -> None:
        if not self.secret_access:
            raise PluginSandboxError("Plugin sandbox denies secret access by default")

    def check_permission(self, permission: str | PluginPermission) -> PluginPermission:
        checked = validate_permission(permission)
        if checked.value in self.denied_permissions or checked not in self.allowed_permissions:
            raise PluginSandboxError(f"Plugin sandbox blocked permission: {checked.value}")
        return checked

    def validate_payload_size(self, payload: Any) -> None:
        encoded = json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
        if len(encoded) > self.payload_size_limits:
            raise PluginSandboxError("Plugin payload exceeds configured sandbox size limit")

    def assert_can_execute(
        self,
        permission: str | PluginPermission | None = None,
        payload: Any | None = None,
        *,
        dry_run: bool = True,
    ) -> None:
        if self.dry_run_required and not dry_run:
            raise PluginSandboxError("Plugin sandbox requires dry-run execution")
        if permission is not None:
            self.check_permission(permission)
        if payload is not None:
            self.validate_payload_size(payload)
