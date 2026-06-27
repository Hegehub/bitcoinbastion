"""Storage profile expectations for future deployment modes."""

from enum import StrEnum

from app.storage.constants import (
    CLICKHOUSE,
    DUCKDB,
    OBJECT_STORAGE,
    POSTGRES,
    QDRANT,
    REDIS,
    SQLITE,
    TIMESCALE,
)
from app.storage.errors import StorageConfigurationError


class StorageProfile(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    SINGLE_NODE = "single_node"
    INITIAL_PRODUCTION = "initial_production"
    FULL_PRODUCTION = "full_production"
    ENTERPRISE_SELF_HOSTED = "enterprise_self_hosted"
    AIR_GAPPED = "air_gapped"


PROFILE_EXPECTED_ENGINES: dict[str, set[str]] = {
    StorageProfile.DEVELOPMENT.value: {POSTGRES, REDIS},
    StorageProfile.TEST.value: {POSTGRES, REDIS},
    StorageProfile.SINGLE_NODE.value: {POSTGRES, REDIS, OBJECT_STORAGE, SQLITE, DUCKDB},
    StorageProfile.INITIAL_PRODUCTION.value: {POSTGRES, REDIS, OBJECT_STORAGE},
    StorageProfile.FULL_PRODUCTION.value: {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
        TIMESCALE,
        CLICKHOUSE,
        QDRANT,
    },
    StorageProfile.ENTERPRISE_SELF_HOSTED.value: {
        POSTGRES,
        REDIS,
        OBJECT_STORAGE,
        TIMESCALE,
        CLICKHOUSE,
        QDRANT,
        SQLITE,
        DUCKDB,
    },
    StorageProfile.AIR_GAPPED.value: {POSTGRES, REDIS, OBJECT_STORAGE, SQLITE, DUCKDB},
}


def get_expected_engines_for_profile(profile: str) -> set[str]:
    """Return required storage engines for a profile, or raise a safe config error."""
    normalized = profile.strip().lower()
    try:
        return set(PROFILE_EXPECTED_ENGINES[normalized])
    except KeyError as exc:
        raise StorageConfigurationError(
            f"Unknown storage profile: {normalized or '<blank>'}"
        ) from exc


def validate_storage_profile(profile: str, enabled_engines: set[str]) -> list[str]:
    """Return human-readable warnings for missing or risky profile configuration."""
    expected = get_expected_engines_for_profile(profile)
    normalized_enabled = {engine.strip().lower() for engine in enabled_engines}
    warnings: list[str] = []

    for engine in sorted(expected - normalized_enabled):
        warnings.append(f"{profile} profile expects {engine} but it is not enabled")

    if REDIS in normalized_enabled:
        warnings.append("redis is enabled but must not be treated as durable truth")

    if OBJECT_STORAGE not in normalized_enabled and profile not in {
        StorageProfile.DEVELOPMENT.value,
        StorageProfile.TEST.value,
    }:
        warnings.append("object_storage is missing; proof packet exports will be degraded")

    return warnings
