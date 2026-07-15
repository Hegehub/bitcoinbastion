import logging

import pytest

from app.services.lnurl.encoding import encode_lnurl
from app.services.lnurl.errors import LNURLUnsafeURLError
from app.services.lnurl.redaction import redact_lnurl_url, redact_lnurl_value
from app.services.lnurl.url_safety import LNURLURLPolicy, validate_lnurl_url

SENTINELS = [
    "raw-k1-secret", "raw-sig-secret", "raw-key-secret", "lnbc1rawinvoice", "raw-preimage", "raw-payerdata", "raw-session-token", "raw-access-pass", "raw-withdraw-id",
]

def test_redaction_removes_sensitive_query_values_and_encoded_lnurl() -> None:
    url = "https://auth.example/cb?k1=raw-k1-secret&sig=raw-sig-secret&key=raw-key-secret&pr=lnbc1rawinvoice&preimage=raw-preimage&payerData=raw-payerdata&session_token=raw-session-token&access_pass=raw-access-pass&withdraw_id=raw-withdraw-id"
    redacted = redact_lnurl_url(url)
    encoded = encode_lnurl("https://example.com/cb?k1=raw-k1-secret", policy=LNURLURLPolicy.remote_fetch())
    assert redact_lnurl_value(encoded).startswith("[REDACTED-LNURL:")
    for sentinel in SENTINELS:
        assert sentinel not in redacted
        assert sentinel not in redact_lnurl_value(encoded)


def test_models_and_exceptions_do_not_reveal_query_secrets() -> None:
    validated = validate_lnurl_url("https://example.com/cb?k1=raw-k1-secret", policy=LNURLURLPolicy.remote_fetch())
    assert "raw-k1-secret" not in repr(validated)
    with pytest.raises(LNURLUnsafeURLError) as exc:
        validate_lnurl_url("https://example.com/%0d%0aInjected?k1=raw-k1-secret", policy=LNURLURLPolicy.remote_fetch())
    assert "raw-k1-secret" not in str(exc.value)


def test_captured_logs_can_use_redacted_values(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("lnurl-test")
    with caplog.at_level(logging.INFO):
        logger.info("lnurl_url=%s", redact_lnurl_url("https://example.com/cb?k1=raw-k1-secret&sig=raw-sig-secret"))
    assert "raw-k1-secret" not in caplog.text
    assert "raw-sig-secret" not in caplog.text
