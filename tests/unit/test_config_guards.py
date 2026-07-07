import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_default_secret_allowed_in_dev() -> None:
    settings = Settings(ENVIRONMENT="dev", JWT_SECRET_KEY="change-me-in-prod")
    assert settings.jwt_secret_key == "change-me-in-prod"


def test_legacy_jwt_secret_no_longer_controls_production_auth() -> None:
    settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="change-me-in-prod")
    assert settings.jwt_secret_key == "change-me-in-prod"


def test_access_server_pepper_setting_is_available() -> None:
    settings = Settings(ACCESS_SERVER_PEPPER="secret-pepper")
    assert settings.access_server_pepper == "secret-pepper"


def test_env_file_path_is_stable() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.api_prefix.startswith("/")


def test_legacy_jwt_algorithm_and_issuer_are_transitional_only() -> None:
    settings = Settings(ENVIRONMENT="prod", JWT_ALGORITHM="HS512", JWT_ISSUER="")
    assert settings.jwt_algorithm == "HS512"
    assert settings.jwt_issuer == ""


def test_cors_allow_origins_parses_comma_separated_values() -> None:
    settings = Settings(CORS_ALLOW_ORIGINS="http://localhost:3000, https://bitcoinbastion.org")
    assert settings.cors_allow_origins == ["http://localhost:3000", "https://bitcoinbastion.org"]


def test_cors_allow_origins_defaults_when_blank() -> None:
    settings = Settings(CORS_ALLOW_ORIGINS="")
    assert settings.cors_allow_origins == ["http://localhost:3000"]


def test_cors_wildcard_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(CORS_ALLOW_ORIGINS="*")
