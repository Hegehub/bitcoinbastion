from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.plugins.base import PluginType
from app.plugins.errors import PluginManifestError, PluginPermissionError
from app.plugins.permissions import PluginPermission, validate_permissions

SENSITIVE_TERMS: tuple[str, ...] = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing material",
    "recovery phrase",
    "12 words",
    "24 words",
)
PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,63}$")


def _contains_sensitive_text(value: Any) -> bool:
    text = str(value).lower()
    return any(term in text for term in SENSITIVE_TERMS)


class PluginManifest(BaseModel):
    model_config = ConfigDict(use_enum_values=False, frozen=True)

    plugin_id: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=500)
    plugin_type: PluginType
    entrypoint: str = Field(min_length=1, max_length=200)
    permissions: tuple[PluginPermission, ...] = ()
    capabilities: tuple[str, ...] = ()
    limitations: tuple[str, ...] = (
        "Plugin execution is controlled by deny-by-default permissions and sandbox policy.",
    )
    safety_flags: dict[str, bool] = Field(
        default_factory=lambda: {
            "no_custody": True,
            "no_signing": True,
            "dry_run_first": True,
            "operator_approval_required": True,
        }
    )
    enabled_by_default: bool = False
    requires_operator_approval: bool = True
    supports_dry_run: bool = True

    @field_validator("plugin_id")
    @classmethod
    def validate_plugin_id(cls, value: str) -> str:
        if not PLUGIN_ID_PATTERN.match(value):
            raise ValueError(
                "plugin_id must be lowercase and contain only letters, numbers, _, -, or ."
            )
        return value

    @field_validator("permissions", mode="before")
    @classmethod
    def validate_manifest_permissions(cls, value: object) -> tuple[PluginPermission, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("permissions must be a list of explicit plugin permissions")
        try:
            return validate_permissions(value)
        except PluginPermissionError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("capabilities", "limitations", mode="before")
    @classmethod
    def normalize_string_tuple(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,)
        if not isinstance(value, (list, tuple, set)):
            raise ValueError("value must be a list of strings")
        normalized = tuple(str(item) for item in value)
        if any(not item.strip() for item in normalized):
            raise ValueError("empty strings are not allowed")
        return normalized

    @model_validator(mode="after")
    def reject_sensitive_manifest_text(self) -> "PluginManifest":
        fields_to_scan = (
            self.plugin_id,
            self.name,
            self.description,
            self.entrypoint,
            " ".join(self.capabilities),
            " ".join(self.limitations),
        )
        if any(_contains_sensitive_text(value) for value in fields_to_scan):
            raise PluginManifestError(
                "Plugin manifests cannot request or describe seed phrases, private keys, "
                "wallet files, xprv/yprv/zprv, or signing material."
            )
        return self
