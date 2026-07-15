from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.services.lnurl.errors import LNURLK1ConsumedError
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1Purpose, LNURLK1RegistryService


def test_integration_atomic_consume_allows_one_success_for_ten_callbacks() -> None:
    svc = LNURLK1RegistryService(config=LNURLK1Config(server_pepper="test-pepper", allow_test_pepper=True), repository=InMemoryK1Repository(), clock=lambda: datetime(2026, 7, 15, tzinfo=UTC))
    issued = svc.issue_k1(LNURLK1Purpose.LNURL_AUTH_STEP_UP, "auth.example", lnurl_action="auth", internal_action="create_api_key", policy_hash="sha256:policy")
    def consume() -> str:
        try:
            svc.consume_k1(issued.k1, expected_policy_hash="sha256:policy")
            return "success"
        except LNURLK1ConsumedError:
            return "replay"
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: consume(), range(10)))
    assert results.count("success") == 1
    assert results.count("replay") == 9
