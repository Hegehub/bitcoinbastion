from typing import NoReturn

from app.core.exceptions import AppError
from app.schemas.auth import LoginRequest, RegisterRequest

LEGACY_AUTH_REPLACEMENT = "/api/v1/access/payment-intents"
LEGACY_AUTH_DISABLED_MESSAGE = (
    "Legacy email/password authentication is disabled. Use Bastion Proof-of-Access."
)


class LegacyAuthDisabledError(AppError):
    def __init__(self) -> None:
        super().__init__(
            message=LEGACY_AUTH_DISABLED_MESSAGE,
            status_code=410,
            code="legacy_auth_disabled",
        )


class AuthService:
    """Disabled legacy auth facade retained only for import stability."""

    def __init__(self, repo: object | None = None) -> None:
        self.repo = repo

    def _raise_disabled(self) -> NoReturn:
        raise LegacyAuthDisabledError()

    def register(self, payload: RegisterRequest) -> NoReturn:
        """Legacy password registration is disabled and never creates accounts."""
        self._raise_disabled()

    def login(self, payload: LoginRequest) -> NoReturn:
        """Legacy password login is disabled and never returns bearer tokens."""
        self._raise_disabled()
