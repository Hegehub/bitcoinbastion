from datetime import UTC, datetime, timedelta

import pytest

from app.domain.lnurl.auth import LNURLAuthAction
from app.services.lnurl.auth_challenge_service import (
    LNURL_AUTH_SIGNATURE_WARNING,
    InMemoryLNURLAuthChallengeRepository,
    LNURLAuthChallengeConfig,
    LNURLAuthChallengeService,
    LNURLAuthChallengeStatus,
    safe_auth_challenge_log_fields,
)
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.errors import LNURLAuthActionNotAllowedError, LNURLAuthConfigurationError, LNURLAuthDomainError, LNURLAuthPolicyPrecheckError
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1RegistryService

NOW = datetime(2026, 7, 15, tzinfo=UTC)

class DenyPolicy:
    def check(self, **kwargs):
        raise RuntimeError("denied")

def _service(*, events=None, clock=lambda: NOW, policy=None) -> LNURLAuthChallengeService:
    k1 = LNURLK1RegistryService(config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True), repository=InMemoryK1Repository(), clock=clock)
    return LNURLAuthChallengeService(config=LNURLAuthChallengeConfig(), k1_registry=k1, repository=InMemoryLNURLAuthChallengeRepository(), clock=clock, policy_precheck=policy, audit_emitter=(lambda e, p: events.append((e, p))) if events is not None else None)


def test_valid_login_register_link_and_auth_challenges_are_created() -> None:
    svc = _service()
    login = svc.create_challenge(action=LNURLAuthAction.LOGIN, origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    register = svc.create_challenge(action=LNURLAuthAction.REGISTER, origin="https://bitcoin-bastion.com", device_key_fingerprint="sha256:device", policy_hash="sha256:policy", risk_level="medium")
    link = svc.create_challenge(action=LNURLAuthAction.LINK, origin="https://bitcoin-bastion.com", device_key_fingerprint="sha256:device", policy_hash="sha256:policy", risk_level="medium")
    auth = svc.create_challenge(action=LNURLAuthAction.AUTH, origin="https://bitcoin-bastion.com", device_key_fingerprint="sha256:device", policy_hash="sha256:policy", risk_level="high", requested_scopes=["metrics:read"])
    assert {login.action, register.action, link.action, auth.action} == {LNURLAuthAction.LOGIN, LNURLAuthAction.REGISTER, LNURLAuthAction.LINK, LNURLAuthAction.AUTH}
    assert login.expires_at == NOW + timedelta(seconds=300)
    assert LNURL_AUTH_SIGNATURE_WARNING in login.display.warning
    decoded = decode_lnurl(login.lnurl, policy=svc.config.url_policy())
    assert decoded.normalized_url == login.callback_url
    assert "k1=" in login.callback_url and "action=login" in login.callback_url
    assert login.qr_payload == login.lnurl


def test_security_bindings_are_stored_server_side_not_in_callback_url_or_response_repr() -> None:
    events = []
    svc = _service(events=events)
    result = svc.create_challenge(action="auth", origin="https://bitcoin-bastion.com", device_key_fingerprint="sha256:device", principal_hint_hash="hmac-sha256:principal", policy_hash="sha256:policy", requested_scopes=["market:read", "trace:read"], risk_level="high", request_context={"object_id": "secret-object"})
    record = svc.repository.get(result.challenge_id)
    assert record is not None
    assert record.lnurl_action is LNURLAuthAction.AUTH
    assert record.internal_action == "wallet_sensitive_action_step_up"
    assert record.origin == "https://bitcoin-bastion.com"
    assert record.auth_domain == "auth.bitcoin-bastion.com"
    assert record.policy_hash == "sha256:policy"
    assert record.device_key_fingerprint == "sha256:device"
    assert record.principal_hint_hash == "hmac-sha256:principal"
    assert record.requested_scopes == ("market:read", "trace:read")
    assert "market:read" not in result.callback_url
    assert "principal" not in result.callback_url
    assert "secret-object" not in repr(record)
    assert events and events[0][0] == "lnurl_auth_challenge_created"
    assert "k1=" not in repr(events)
    assert result.lnurl not in repr(events)


def test_unsupported_action_unsafe_config_invalid_inputs_and_policy_denial_fail_closed() -> None:
    svc = _service()
    with pytest.raises(LNURLAuthActionNotAllowedError):
        svc.create_challenge(action="create_api_key", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="high")
    with pytest.raises(LNURLAuthConfigurationError):
        LNURLAuthChallengeConfig(public_base_url="http://auth.bitcoin-bastion.com")
    with pytest.raises(LNURLAuthConfigurationError):
        LNURLAuthChallengeConfig(public_base_url="")
    with pytest.raises(LNURLAuthActionNotAllowedError):
        svc.create_challenge(action="register", origin="https://bitcoin-bastion.com", device_key_fingerprint="dev-not-hash", policy_hash="sha256:policy", risk_level="medium")
    with pytest.raises(LNURLAuthConfigurationError):
        svc.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium", expires_in_seconds=999)
    with pytest.raises(LNURLAuthDomainError):
        svc.create_challenge(action="login", origin="https://evil.example", policy_hash="sha256:policy", risk_level="medium")
    with pytest.raises(LNURLAuthPolicyPrecheckError):
        _service(policy=DenyPolicy()).create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")


def test_lifecycle_retrieval_cancellation_expiration_and_idempotency() -> None:
    now = {"value": NOW}
    svc = _service(clock=lambda: now["value"])
    first = svc.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium", idempotency_key="same")
    second = svc.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium", idempotency_key="same")
    assert second.challenge_id == first.challenge_id
    view = svc.get_challenge(first.challenge_id)
    assert view.status is LNURLAuthChallengeStatus.PENDING
    assert view.qr_payload == first.qr_payload
    cancelled = svc.cancel_challenge(first.challenge_id, reason="user_cancelled")
    assert cancelled.status is LNURLAuthChallengeStatus.CANCELLED
    assert svc.cancel_challenge(first.challenge_id, reason="user_cancelled").status is LNURLAuthChallengeStatus.CANCELLED
    exp = svc.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy2", risk_level="medium")
    now["value"] = NOW + timedelta(seconds=301)
    assert svc.get_challenge(exp.challenge_id).status is LNURLAuthChallengeStatus.EXPIRED
    assert svc.get_challenge(exp.challenge_id).qr_payload is None


def test_safe_log_fields_redact_callback_and_lnurl() -> None:
    svc = _service()
    result = svc.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    record = svc.repository.get(result.challenge_id)
    fields = safe_auth_challenge_log_fields(record)
    assert "[REDACTED]" in fields["callback_url"] or "%5BREDACTED%5D" in fields["callback_url"]
    assert fields["lnurl"].startswith("[REDACTED-LNURL:")
    assert result.callback_url not in repr(fields)
