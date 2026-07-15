from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from app.services.lnurl.errors import LNURLK1ActionMismatchError, LNURLK1BindingMismatchError, LNURLK1ConsumedError, LNURLK1DomainMismatchError, LNURLK1PolicyMismatchError
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1Purpose, LNURLK1RegistryService, LNURLK1Status
from app.services.lnurl.replay_protection import LNURLK1ReplayProtection

NOW = datetime(2026, 7, 15, tzinfo=UTC)

def _service(events=None, metrics=None) -> LNURLK1RegistryService:
    return LNURLK1RegistryService(config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True), repository=InMemoryK1Repository(), clock=lambda: NOW, audit_emitter=(lambda e, p: events.append((e, p))) if events is not None else None, metrics_emitter=(lambda n, labels: metrics.append((n, labels))) if metrics is not None else None)


def _issued(svc: LNURLK1RegistryService):
    return svc.issue_k1(
        LNURLK1Purpose.LNURL_AUTH_STEP_UP,
        "auth.example",
        lnurl_action="auth",
        internal_action="create_api_key",
        policy_hash="sha256:policy",
        principal_hash="hmac-sha256:principal",
        device_key_fingerprint="sha256:device",
        session_hash="hmac-sha256:session",
        payment_request_hash="sha256:payment",
        withdraw_request_hash="sha256:withdraw",
        recovery_attempt_hash="sha256:recovery",
    )


def test_valid_challenge_consumed_once_and_terminal() -> None:
    events = []
    metrics = []
    svc = _service(events, metrics)
    issued = _issued(svc)
    ctx = svc.consume_k1(issued.k1, expected_purpose="lnurl_auth_step_up", expected_lnurl_action="auth", expected_internal_action="create_api_key", expected_domain="auth.example", expected_policy_hash="sha256:policy")
    assert ctx.registry_id == issued.registry_id
    assert svc.get_k1_status(issued.k1).status is LNURLK1Status.CONSUMED
    with pytest.raises(LNURLK1ConsumedError):
        svc.consume_k1(issued.k1)
    assert any(event == "lnurl_k1_consumed" for event, _ in events)
    assert any(name == "lnurl_k1_replay_rejected_total" for name, _ in metrics)


@pytest.mark.parametrize("kwargs,exc", [
    ({"expected_purpose": "lnurl_auth_login"}, LNURLK1ActionMismatchError),
    ({"expected_lnurl_action": "login"}, LNURLK1ActionMismatchError),
    ({"expected_internal_action": "recovery_complete"}, LNURLK1ActionMismatchError),
    ({"expected_domain": "evil.example"}, LNURLK1DomainMismatchError),
    ({"expected_policy_hash": "sha256:other"}, LNURLK1PolicyMismatchError),
    ({"expected_principal_hash": "hmac-sha256:other"}, LNURLK1BindingMismatchError),
    ({"expected_device_key_fingerprint": "sha256:other"}, LNURLK1BindingMismatchError),
    ({"expected_session_hash": "hmac-sha256:other"}, LNURLK1BindingMismatchError),
    ({"expected_payment_request_hash": "sha256:other"}, LNURLK1BindingMismatchError),
    ({"expected_withdraw_request_hash": "sha256:other"}, LNURLK1BindingMismatchError),
    ({"expected_recovery_attempt_hash": "sha256:other"}, LNURLK1BindingMismatchError),
])
def test_binding_mismatches_fail_before_consumption(kwargs, exc) -> None:
    svc = _service()
    issued = _issued(svc)
    with pytest.raises(exc):
        svc.consume_k1(issued.k1, **kwargs)
    assert svc.get_k1_status(issued.k1).status is LNURLK1Status.ACTIVE


def test_concurrent_consume_allows_exactly_one_success() -> None:
    svc = _service()
    issued = _issued(svc)
    gate_errors = []
    def consume():
        try:
            svc.consume_k1(issued.k1, expected_policy_hash="sha256:policy")
            return "success"
        except LNURLK1ConsumedError:
            return "replay"
        except Exception as exc:  # pragma: no cover - debug aid
            gate_errors.append(exc)
            return "other"
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: consume(), range(10)))
    assert gate_errors == []
    assert results.count("success") == 1
    assert results.count("replay") == 9


def test_replay_protection_facade_uses_registry_atomic_consume() -> None:
    svc = _service()
    issued = _issued(svc)
    facade = LNURLK1ReplayProtection(svc)
    facade.consume_once(issued.k1, expected_policy_hash="sha256:policy")
    with pytest.raises(LNURLK1ConsumedError):
        facade.consume_once(issued.k1, expected_policy_hash="sha256:policy")


def test_failure_policy_revocation_expiration_and_bulk_revoke() -> None:
    svc = _service()
    login = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login", principal_hash="p")
    assert svc.record_k1_failure(login.k1, "invalid_signature").failure_count == 1
    assert svc.record_k1_failure(login.k1, "invalid_signature").failure_count == 2
    terminal = svc.record_k1_failure(login.k1, "invalid_signature")
    assert terminal.terminal is True
    critical = _issued(svc)
    assert svc.record_k1_failure(critical.k1, "invalid_signature").terminal is True
    active = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", lnurl_action="login", principal_hash="p")
    assert svc.revoke_active_k1_for_binding(principal_hash="p", reason_code="principal_revoked") >= 1
    assert svc.revoke_k1(raw_k1=active.k1, reason_code="repeat").revoked is False
    stale = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_LOGIN, "auth.example", ttl_seconds=1)
    assert svc.expire_stale_k1(now=NOW + timedelta(seconds=2)) >= 1
    assert svc.get_k1_status(stale.k1).status is LNURLK1Status.EXPIRED
