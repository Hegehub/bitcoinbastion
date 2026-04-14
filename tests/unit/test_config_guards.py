import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_default_secret_allowed_in_dev() -> None:
    settings = Settings(ENVIRONMENT="dev", JWT_SECRET_KEY="change-me-in-prod")
    assert settings.jwt_secret_key == "change-me-in-prod"


def test_default_secret_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="change-me-in-prod")


def test_short_secret_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="prod", JWT_SECRET_KEY="short-secret")


def test_strong_secret_allowed_in_production() -> None:
    strong_secret = "bastion-prod-secret-that-is-long-and-random-2026"
    settings = Settings(ENVIRONMENT="prod", JWT_SECRET_KEY=strong_secret)
    assert settings.jwt_secret_key == strong_secret


def test_env_file_path_is_stable() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.api_prefix.startswith("/")
