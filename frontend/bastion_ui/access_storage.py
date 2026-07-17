from __future__ import annotations

from dataclasses import dataclass

RAW_ACCESS_PASS_LOCAL_STORAGE_ALLOWED = False
RECOVERY_PHRASE_LOCAL_STORAGE_ALLOWED = False
PRIVATE_KEY_LOCAL_STORAGE_ALLOWED = False
PRODUCTION_DEV_SIGNER_ALLOWED = False
SESSION_STORAGE_STRATEGY = "memory_or_secure_session_storage"


@dataclass(frozen=True)
class AccessStoragePolicy:
    raw_access_pass_local_storage_allowed: bool = RAW_ACCESS_PASS_LOCAL_STORAGE_ALLOWED
    recovery_phrase_local_storage_allowed: bool = RECOVERY_PHRASE_LOCAL_STORAGE_ALLOWED
    private_key_local_storage_allowed: bool = PRIVATE_KEY_LOCAL_STORAGE_ALLOWED
    session_storage_strategy: str = SESSION_STORAGE_STRATEGY


def dev_signer_allowed(environment: str, enabled: bool) -> bool:
    """Return whether the development-only signer may be used."""

    return enabled and environment.lower() not in {"production", "prod"}
