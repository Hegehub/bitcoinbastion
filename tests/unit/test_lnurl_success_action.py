from __future__ import annotations

import pytest

from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLSuccessActionType
from app.schemas.lnurl_success_action import LNURLMessageSuccessAction, LNURLURLSuccessAction
from app.services.lnurl.success_action import LNURLSuccessActionConfig, LNURLSuccessActionService


def make_service(**kwargs):
    values = {"base_url": "https://pay.example.com", "allowed_hosts": frozenset({"pay.example.com"})}
    values.update(kwargs)
    config = LNURLSuccessActionConfig(**values)
    return LNURLSuccessActionService(config=config)


def test_message_action_accepted():
    action = LNURLMessageSuccessAction(message="Payment complete. Bastion will verify your activation.")
    assert action.tag == "message"


def test_url_action_accepted():
    action = LNURLURLSuccessAction(description="Open Bastion", url="https://pay.example.com/access/activate/abc")
    assert action.tag == "url"


@pytest.mark.parametrize("message", ["", "x" * 145, "hello\x00world"])
def test_invalid_message_rejected(message):
    with pytest.raises(ValueError):
        LNURLMessageSuccessAction(message=message)


def test_description_over_144_rejected():
    with pytest.raises(ValueError):
        LNURLURLSuccessAction(description="x" * 145, url="https://pay.example.com/access/activate/abc")


def test_unsupported_tag_rejected():
    with pytest.raises(ValueError):
        LNURLMessageSuccessAction.model_validate({"tag": "aes", "message": "ok"})


def test_different_url_domain_rejected():
    service = make_service()
    with pytest.raises(ValueError, match="success_action_domain_mismatch"):
        service.build_url_action(
            description="Open Bastion",
            raw_reference="lnact_abc",
            callback_origin="https://evil.example.com/lnurl/callback",
            purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        )


@pytest.mark.parametrize("url", [
    "https://user:pass@pay.example.com/access/activate/abc",
    "https://pay.example.com/access/activate/abc?access_pass=raw",
    "https://pay.example.com/access/activate/abc?session_token=raw",
    "https://pay.example.com/access/activate/abc?recovery=seed",
])
def test_url_secrets_or_credentials_rejected(url):
    with pytest.raises(ValueError):
        LNURLURLSuccessAction(description="Open Bastion", url=url)


def test_unsafe_scheme_rejected():
    service = make_service(base_url="http://pay.example.com")
    with pytest.raises(ValueError, match="unsafe_success_action_url"):
        service.build_url_action(
            description="Open Bastion",
            raw_reference="lnact_abc",
            callback_origin="https://pay.example.com/lnurl/callback",
            purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        )


def test_arbitrary_client_url_rejected():
    service = make_service()
    with pytest.raises(ValueError):
        service.validate_safe_target_path("/redirect/https://evil.example")


def test_server_controlled_route_accepted():
    service = make_service()
    action = service.build_url_action(
        description="Open Bastion",
        raw_reference="lnact_abc",
        callback_origin="https://pay.example.com/lnurl/callback",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
    )
    assert action["url"] == "https://pay.example.com/access/activate/lnact_abc"


def test_message_does_not_claim_activation_before_readiness():
    with pytest.raises(ValueError, match="misleading_success_action_message"):
        make_service().build_message_action("Pro Pass activated")


def test_same_callback_host_accepted():
    assert make_service().validate_callback_domain("https://pay.example.com/lnurl/callback") == "pay.example.com"


def test_onion_http_rejected_when_onion_mode_disabled():
    service = make_service(base_url="http://abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcd.onion", allowed_hosts=frozenset({"abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcd.onion"}))
    with pytest.raises(ValueError):
        service.validate_callback_domain("http://abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcd.onion/lnurl")


@pytest.mark.anyio
async def test_render_url_fragment_and_hashes_reference_at_rest():
    service = make_service()
    action = await service.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_1",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl/callback",
        action_type=LNURLSuccessActionType.URL,
    )
    assert action["tag"] == "url"
    assert "/access/activate/lnact_" in action["url"]
    records = await service.repository.get_by_payment_request_id("lpay_1")
    assert records[0].activation_reference_hash.startswith("hmac-sha256:")
    assert "lnact_" not in records[0].activation_reference_hash
