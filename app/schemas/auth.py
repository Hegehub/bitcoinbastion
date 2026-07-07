from pydantic import BaseModel, Field

LEGACY_AUTH_DISABLED_MESSAGE = (
    "Legacy email/password authentication is disabled. Use Bastion Proof-of-Access."
)
LEGACY_AUTH_REPLACEMENT = "/api/v1/access/payment-intents"


class LegacyAuthDisabledSchema(BaseModel):
    """Compatibility schema for disabled legacy auth responses."""

    code: str = "legacy_auth_disabled"
    message: str = LEGACY_AUTH_DISABLED_MESSAGE
    replacement: str = LEGACY_AUTH_REPLACEMENT


class RegisterRequest(BaseModel):
    """Deprecated compatibility stub; password registration is disabled."""

    deprecated: bool = Field(default=True, description="Legacy registration is disabled.")
    replacement: str = LEGACY_AUTH_REPLACEMENT


class LoginRequest(BaseModel):
    """Deprecated compatibility stub; username/password login is disabled."""

    deprecated: bool = Field(default=True, description="Legacy login is disabled.")
    replacement: str = LEGACY_AUTH_REPLACEMENT


class TokenResponse(BaseModel):
    """Deprecated compatibility stub; bearer tokens are never issued."""

    code: str = "legacy_auth_disabled"
    message: str = LEGACY_AUTH_DISABLED_MESSAGE
    replacement: str = LEGACY_AUTH_REPLACEMENT
