from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeConfig, LNURLAuthChallengeService
from app.services.lnurl.errors import LNURLAuthActionNotAllowedError, LNURLAuthConfigurationError
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1RegistryService

NOW = datetime(2026, 7, 15, tzinfo=UTC)


def _service(*, events=None) -> LNURLAuthChallengeService:
    registry = LNURLK1RegistryService(
        config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True),
        repository=InMemoryK1Repository(),
        clock=lambda: NOW,
    )
    return LNURLAuthChallengeService(
        config=LNURLAuthChallengeConfig(),
        k1_registry=registry,
        clock=lambda: NOW,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
    )


def _challenge_k1(callback_url: str) -> str:
    parsed = urlsplit(callback_url)
    return parse_qs(parsed.query)["k1"][0]


def test_k1_is_unique_and_not_predictable_sequence() -> None:
    service = _service()
    first = service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    second = service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy2", risk_level="medium")
    assert _challenge_k1(first.callback_url) != _challenge_k1(second.callback_url)
    assert len(_challenge_k1(first.callback_url)) == 64


def test_non_expiring_or_excessive_ttl_and_host_injection_fail_closed() -> None:
    service = _service()
    with pytest.raises(LNURLAuthConfigurationError):
        service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium", expires_in_seconds=0)
    with pytest.raises(LNURLAuthConfigurationError):
        service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium", expires_in_seconds=601)
    with pytest.raises(LNURLAuthConfigurationError):
        LNURLAuthChallengeConfig(public_base_url="https://attacker.example", stable_domain="auth.bitcoin-bastion.com")
    with pytest.raises(LNURLAuthConfigurationError):
        LNURLAuthChallengeConfig(public_base_url="https://auth.bitcoin-bastion.com.evil.example", stable_domain="auth.bitcoin-bastion.com")


def test_audit_and_repr_do_not_expose_raw_k1_or_lnurl() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    service = _service(events=events)
    result = service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    raw_k1 = _challenge_k1(result.callback_url)
    rendered = repr(events) + repr(result)
    assert raw_k1 not in rendered
    assert result.lnurl not in rendered
    assert result.callback_url not in rendered


@pytest.mark.parametrize("key", ["linking_key", "bitcoin_seed", "private_key", "mnemonic", "sig", "signature"])
def test_secrets_signatures_and_wallet_material_are_rejected_at_creation(key: str) -> None:
    service = _service()
    with pytest.raises(LNURLAuthActionNotAllowedError):
        service.create_challenge(
            action="login",
            origin="https://bitcoin-bastion.com",
            policy_hash="sha256:policy",
            risk_level="medium",
            request_context={key: "SENTINEL_SECRET_VALUE"},
        )


def test_challenge_creation_does_not_issue_session_principal_or_entitlement() -> None:
    service = _service()
    result = service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    assert not hasattr(result, "session_token")
    assert not hasattr(result, "principal_hash")
    assert not hasattr(result, "entitlement_id")
    assert result.display.warning
