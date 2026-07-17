from datetime import UTC, datetime, timedelta

import pytest

from app.services.lnurl.errors import LNURLK1ConfigurationError, LNURLK1MalformedError, LNURLK1PolicyMismatchError, LNURLK1RevokedError, LNURLK1UnknownError
from app.services.lnurl.k1_registry import (
    K1_BYTES,
    K1_HEX_LENGTH,
    InMemoryK1Repository,
    LNURLK1Config,
    LNURLK1Purpose,
    LNURLK1RegistryService,
    LNURLK1Status,
    generate_k1,
    validate_k1_format,
)

NOW = datetime(2026, 7, 15, tzinfo=UTC)

class Clock:
    def __init__(self) -> None:
        self.now = NOW
    def __call__(self) -> datetime:
        return self.now


def _service(*, clock: Clock | None = None, audit=None, metrics=None) -> LNURLK1RegistryService:
    return LNURLK1RegistryService(config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True), repository=InMemoryK1Repository(), clock=clock or Clock(), audit_emitter=audit, metrics_emitter=metrics)


def test_generate_k1_is_32_bytes_lowercase_hex_and_unique() -> None:
    first = generate_k1()
    second = generate_k1()
    assert len(first) == K1_HEX_LENGTH
    assert bytes.fromhex(first) and len(bytes.fromhex(first)) == K1_BYTES
    assert first == first.lower()
    assert first != second


@pytest.mark.parametrize("value", ["", "A" * 64, "g" * 64, "0" * 63, "0" * 65])
def test_invalid_k1_format_rejected(value: str) -> None:
    with pytest.raises(LNURLK1MalformedError):
        validate_k1_format(value)


def test_issue_stores_hmac_lookup_not_raw_k1_and_sets_bindings() -> None:
    svc = _service()
    issued = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "Auth.Example.", lnurl_action="login", internal_action="wallet_principal_authenticate", policy_hash="sha256:policy")
    record = svc.repository.get(svc._lookup_hash(issued.k1))
    assert record is not None
    assert record.k1_lookup_hash.startswith("hmac-sha256:")
    assert record.k1_fingerprint.startswith("sha256:")
    assert issued.k1 not in repr(record)
    assert record.expected_domain == "auth.example"
    assert record.lnurl_action == "login"
    assert record.internal_action == "wallet_principal_authenticate"
    assert record.policy_hash == "sha256:policy"
    assert issued.expires_at == NOW + timedelta(seconds=300)


def test_ttl_by_purpose_and_critical_policy_hash_required() -> None:
    svc = _service()
    step = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_STEP_UP, "auth.example", lnurl_action="auth", internal_action="create_api_key", policy_hash="sha256:p")
    assert step.expires_at == NOW + timedelta(seconds=180)
    with pytest.raises(LNURLK1PolicyMismatchError):
        svc.issue_k1(LNURLK1Purpose.LNURL_WITHDRAW, "auth.example", lnurl_action="withdrawRequest")
    with pytest.raises(LNURLK1ConfigurationError):
        svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", ttl_seconds=901)


def test_lookup_active_unknown_expired_revoked_and_consumed_statuses() -> None:
    clock = Clock()
    svc = _service(clock=clock)
    issued = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login")
    assert svc.get_k1_status(issued.k1).status is LNURLK1Status.ACTIVE
    assert svc.get_k1_status("0" * 64).reason_code == "unknown_k1"
    svc.revoke_k1(raw_k1=issued.k1, reason_code="policy_change")
    assert svc.get_k1_status(issued.k1).status is LNURLK1Status.REVOKED
    with pytest.raises(LNURLK1RevokedError):
        svc.consume_k1(issued.k1)
    issued2 = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login")
    clock.now = NOW + timedelta(seconds=301)
    assert svc.get_k1_status(issued2.k1).status is LNURLK1Status.EXPIRED
    with pytest.raises(LNURLK1UnknownError):
        svc.consume_k1("1" * 64)


def test_missing_pepper_fails_closed() -> None:
    with pytest.raises(LNURLK1ConfigurationError):
        LNURLK1Config(server_pepper="")
