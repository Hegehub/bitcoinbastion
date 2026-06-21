import pytest

from app.storage.errors import StorageConfigurationError, StorageSafetyError
from app.storage.redis_boundaries import (
    API_RESPONSE_CACHE,
    CHALLENGE,
    LOCK,
    NONCE,
    PROVIDER_POLLING,
    RATE_LIMIT,
    SESSION_HOT,
    WEBSOCKET_FANOUT,
    build_redis_key,
    require_ttl_for_redis_key,
    validate_redis_purpose,
)


@pytest.mark.parametrize(
    "purpose",
    [RATE_LIMIT, LOCK, NONCE, WEBSOCKET_FANOUT, PROVIDER_POLLING, CHALLENGE, SESSION_HOT],
)
def test_redis_allowed_ephemeral_purposes_pass_validation(purpose: str) -> None:
    validate_redis_purpose(purpose)


@pytest.mark.parametrize(
    "purpose",
    [
        "access_certificates",
        "subscription_entitlements",
        "access_revocations",
        "access_audit_events",
        "access_payment_intents",
        "recovery_quorums",
        "private keys",
        "seed phrase",
        "wallet.dat",
        "xprv",
    ],
)
def test_redis_forbidden_durable_truth_purposes_fail_validation(purpose: str) -> None:
    with pytest.raises(StorageSafetyError):
        validate_redis_purpose(purpose)


@pytest.mark.parametrize("purpose", [LOCK, CHALLENGE, SESSION_HOT, NONCE])
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
    assert build_redis_key("development", RATE_LIMIT, "scope", "identity_hash") == (
        "bb:development:rate:scope:identity_hash"
    )


@pytest.mark.parametrize("part", ["", "wallet.dat", "raw api key", "../escape", "has space"])
def test_build_redis_key_rejects_unsafe_parts(part: str) -> None:
    with pytest.raises((StorageConfigurationError, StorageSafetyError)):
        build_redis_key("production", API_RESPONSE_CACHE, part)
