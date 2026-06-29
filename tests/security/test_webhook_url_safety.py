import pytest

from app.services.events.webhook_service import WebhookService, WebhookServiceError


def service() -> WebhookService:
    return WebhookService.__new__(WebhookService)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://example.com/hook",
        "file:///tmp/hook",
        "ssh://example.com/hook",
        "data:text/plain,hi",
        "http://localhost/hook",
        "http://127.0.0.1/hook",
        "http://10.0.0.1/hook",
        "https://user:pass@example.com/hook",
        "https://example.com/" + "x" * 2050,
    ],
)
def test_unsafe_webhook_urls_are_rejected_by_default(url: str) -> None:
    with pytest.raises(WebhookServiceError):
        service()._validate_target_url(url)


def test_public_https_webhook_url_allowed() -> None:
    assert (
        service()._validate_target_url("https://example.com/bastion")
        == "https://example.com/bastion"
    )
