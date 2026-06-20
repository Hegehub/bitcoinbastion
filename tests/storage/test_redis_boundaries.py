import pytest

from app.storage.errors import StorageConfigurationError, StorageSafetyError
from app.storage.redis_boundaries import (
    ALLOWED_REDIS_PURPOSES,
    CHALLENGE,
    LOCK,
    SESSION_HOT,
    build_redis_key,
    require_ttl_for_redis_key,
    validate_redis_purpose,
)


def test_allowed_purposes_pass_validation() -> None:
    for purpose in ALLOWED_REDIS_PURPOSES:
        validate_redis_purpose(purpose)


@pytest.mark.parametrize(
    "purpose",
    [
        "access_certificates",
        "subscription_entitlements",
        "storage_artifacts",
        "private keys",
        "seed phrase",
        "wallet.dat",
        "xprv",
    ],
)
def test_forbidden_purposes_fail_validation(purpose: str) -> None:
    with pytest.raises(StorageSafetyError):
        validate_redis_purpose(purpose)


@pytest.mark.parametrize("purpose", [LOCK, CHALLENGE, SESSION_HOT])
def test_short_lived_purposes_require_ttl(purpose: str) -> None:
    with pytest.raises(StorageConfigurationError):
        require_ttl_for_redis_key(purpose, None)
    with pytest.raises(StorageConfigurationError):
        require_ttl_for_redis_key(purpose, 0)
    require_ttl_for_redis_key(purpose, 60)


def test_build_redis_key_rejects_empty_purpose() -> None:
    with pytest.raises(StorageConfigurationError):
        build_redis_key("development", "", "abc123")


def test_build_redis_key_includes_environment_prefix() -> None:
    assert build_redis_key("development", "rate", "scope", "identity_hash") == (
        "bb:development:rate:scope:identity_hash"
    )


@pytest.mark.parametrize("part", ["", "wallet.dat", "raw api key", "../escape", "has space"])
def test_build_redis_key_rejects_unsafe_parts(part: str) -> None:
    with pytest.raises((StorageConfigurationError, StorageSafetyError)):
        build_redis_key("production", "cache", part)
