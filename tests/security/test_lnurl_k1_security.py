import logging
from datetime import UTC, datetime

import pytest

from app.services.lnurl.errors import LNURLK1ConsumedError, LNURLK1MalformedError
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1Purpose, LNURLK1RegistryService, validate_k1_format

NOW = datetime(2026, 7, 15, tzinfo=UTC)

def _service(events=None) -> LNURLK1RegistryService:
    return LNURLK1RegistryService(config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True), repository=InMemoryK1Repository(), clock=lambda: NOW, audit_emitter=(lambda e, p: events.append((e, p))) if events is not None else None)


def test_raw_k1_signature_and_keys_absent_from_audit_logs_and_errors(caplog: pytest.LogCaptureFixture) -> None:
    events = []
    svc = _service(events)
    issued = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login", internal_action="wallet_principal_authenticate")
    raw_signature = "raw-sig-secret"
    raw_key = "raw-linking-key-secret"
    with caplog.at_level(logging.INFO):
        logging.getLogger("lnurl-k1-test").info("failure=%s", {"k1_fingerprint": issued.k1_fingerprint, "reason": "invalid_signature"})
    svc.consume_k1(issued.k1)
    with pytest.raises(LNURLK1ConsumedError) as exc:
        svc.consume_k1(issued.k1)
    rendered = repr(events) + caplog.text + str(exc.value)
    assert issued.k1 not in rendered
    assert raw_signature not in rendered
    assert raw_key not in rendered
    assert "k1_fingerprint" in rendered


def test_malformed_random_strings_never_crash_or_leak() -> None:
    for value in ["", "A" * 64, "z" * 64, "0" * 63, "0" * 65, "raw-k1-secret"]:
        with pytest.raises(LNURLK1MalformedError):
            validate_k1_format(value)


def test_k1_does_not_create_principal_session_payment_or_withdraw_side_effects() -> None:
    svc = _service()
    issued = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login")
    ctx = svc.consume_k1(issued.k1)
    assert ctx.principal_hash is None
    assert ctx.session_hash is None
    assert ctx.payment_request_hash is None
    assert ctx.withdraw_request_hash is None
