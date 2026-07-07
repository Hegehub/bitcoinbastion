import pytest

from app.core.exceptions import AppError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth.auth_service import AuthService


def test_register_is_disabled_and_does_not_create_account() -> None:
    service = AuthService(repo=None)

    with pytest.raises(AppError) as exc_info:
        service.register(RegisterRequest())

    assert exc_info.value.code == "legacy_auth_disabled"
    assert exc_info.value.status_code == 410


def test_login_is_disabled_and_does_not_issue_token() -> None:
    service = AuthService(repo=None)

    with pytest.raises(AppError) as exc_info:
        service.login(LoginRequest())

    assert exc_info.value.code == "legacy_auth_disabled"
    assert "access_token" not in TokenResponse.model_fields
