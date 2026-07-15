from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeConfig, LNURLAuthChallengeService
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1RegistryService

NOW = datetime(2026, 7, 15, tzinfo=UTC)


def test_lnurl_auth_challenge_creation_persists_safe_record_and_registers_hashed_k1() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    registry_repo = InMemoryK1Repository()
    registry = LNURLK1RegistryService(
        config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True),
        repository=registry_repo,
        clock=lambda: NOW,
    )
    service = LNURLAuthChallengeService(
        config=LNURLAuthChallengeConfig(),
        k1_registry=registry,
        clock=lambda: NOW,
        audit_emitter=lambda event, payload: events.append((event, payload)),
    )

    result = service.create_challenge(
        action="auth",
        origin="https://bitcoin-bastion.com",
        device_key_fingerprint="sha256:device",
        policy_hash="sha256:policy",
        requested_scopes=["api:create"],
        risk_level="high",
    )

    raw_k1 = parse_qs(urlsplit(result.callback_url).query)["k1"][0]
    record = service.repository.get(result.challenge_id)
    assert record is not None
    assert record.policy_hash == "sha256:policy"
    assert record.device_key_fingerprint == "sha256:device"
    assert raw_k1 in result.callback_url
    registry_records = registry_repo.records()
    assert len(registry_records) == 1
    assert registry_records[0].k1_lookup_hash.startswith("hmac-sha256:")
    assert raw_k1 not in repr(registry_records[0])
    assert events and events[0][0] == "lnurl_auth_challenge_created"
    assert raw_k1 not in repr(events)
    assert not hasattr(result, "session_token")
